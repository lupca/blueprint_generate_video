# Hướng Dẫn Sử Dụng & Kiến Trúc Hệ Thống Gen Video Tự Động (Headless Automation)

Hệ thống này được thiết kế để tự động hóa hoàn toàn quy trình tạo video quảng cáo thương mại 15 giây bằng cách kết hợp **Flux.1 Schnell** (Tạo ảnh nhãn hiệu/keyframe) và **LTX-Video** (Tạo chuyển động từ ảnh keyframe), sau đó tự động ghép các đoạn ngắn thành video hoàn chỉnh mà không tốn tài nguyên GPU cho khâu hậu kỳ.

---

## 1. Kiến Trúc Hệ Thống (Architecture & Data Flow)

Quy trình hoạt động được chia làm 3 tầng chính:

```
+-----------------------------------------------------------------+
| TẦNG ĐIỀU PHỐI (Python Client - generate_video.py)               |
|  - Thiết lập kênh WebSocket lắng nghe cập nhật trạng thái        |
|  - Đẩy cấu hình JSON qua HTTP POST /prompt                      |
|  - Tải file video nhị phân qua HTTP GET /view                   |
+-------------------------------+---------------------------------+
                                | (API JSON / WebSockets)
                                v
+-----------------------------------------------------------------+
| TẦNG TÍNH TOÁN (GPU - ComfyUI Server)                           |
|  1. Flux.1 Schnell GGUF (4 steps, euler) -> Sinh ảnh Keyframe  |
|  2. LTX-Video GGUF (8 steps, euler) -> Nhận Keyframe và Prompt  |
|  3. Tiled VAE Decode -> Giải mã Latent sang Video h264-mp4      |
+-------------------------------+---------------------------------+
                                | (HTTP GET /view)
                                v
+-----------------------------------------------------------------+
| TẦNG HẬU KỲ (CPU - FFmpeg Subprocess)                           |
|  - Khâu nhị phân các luồng bitstream (Concat Demuxer, -c copy)  |
|  - Xuất bản video hoàn chỉnh final_commercial_15s.mp4           |
+-----------------------------------------------------------------+
```

### Cách các mô hình được kết nối trong workflow API:
Thay vì lưu ảnh trung gian ra ổ cứng rồi tải lại (dễ gây nghẽn I/O), ảnh đầu ra (`IMAGE`) từ node **VAE Decode** của mô hình Flux được đấu trực tiếp vào cổng đầu vào `image` của node **LTXVImgToVideoAdvanced**. Điều này giúp dữ liệu truyền trực tiếp trong bộ nhớ VRAM của GPU:
*   `Flux VAE Decode (IMAGE)` -> `LTXVImgToVideoAdvanced (image)`.

---

## 2. Giao Thức API & Cơ Chế Hoạt Động (Headless Automation & WebSockets)

Quá trình điều phối chạy độc lập qua script Python thông qua các endpoint nội bộ của ComfyUI (`127.0.0.1:8188`):

1.  **Khởi tạo kết nối song phương (`/ws`)**:
    Script mở một kết nối WebSocket nối dài đến máy chủ: `ws://127.0.0.1:8188/ws?clientId={UUID}`. Kênh này dùng để lắng nghe trạng thái tiến trình thời gian thực.
2.  **Đệ trình tác vụ (`/prompt`)**:
    Script đọc cấu hình đồ thị từ `workflow_api.json`, điền văn bản kịch bản (prompt) tương ứng vào node `"6"` (Flux) và node `"22"` (LTX-Video), sau đó gửi yêu cầu HTTP POST đến `/prompt` và nhận về một `prompt_id` (UUID tác vụ).
3.  **Lắng nghe sự kiện (Event Interception)**:
    Thay vì sử dụng hàm chờ thụ động `time.sleep()`, client liên tục đọc gói tin từ WebSocket. Khi nhận được gói tin có cấu trúc:
    `{"type": "executing", "data": {"node": null, "prompt_id": "<prompt_id>"}}`
    Hệ thống hiểu rằng GPU đã xử lý xong hoàn toàn tác vụ đó.
4.  **Xử lý Ngoại lệ / Timeout Fallback**:
    Để chống treo luồng khi mất kết nối mạng, script được cài đặt timeout **5 phút** cho mỗi segment. Nếu hết thời gian hoặc mất kết nối, hệ thống tự động chuyển sang cơ chế **Polling**. Client sẽ gửi lệnh HTTP GET đến endpoint `/history/{prompt_id}` mỗi 5 giây để kiểm tra xem tác vụ đã hoàn thành trên server hay chưa.
5.  **Tải Video nhị phân (`/view`)**:
    Khi lịch sử xác nhận hoàn tất, client phân tích tên tệp video từ API history và gửi HTTP GET đến `/view?filename=...` để kéo dòng dữ liệu nhị phân về đĩa cứng thành các phân đoạn `part1.mp4`, `part2.mp4`, `part3.mp4`.

---

## 3. Khâu Hậu Kỳ Thần Tốc (FFmpeg Concat)

Sau khi có đủ 3 video ngắn 5 giây, script tự động ghi danh sách tệp vào `inputs.txt`:
```
file '/root/part1.mp4'
file '/root/part2.mp4'
file '/root/part3.mp4'
```
Sau đó, triệu gọi FFmpeg bằng lệnh:
```bash
ffmpeg -y -f concat -safe 0 -i inputs.txt -c copy final_commercial_15s.mp4
```
**Tại sao cách này nhanh?**
Tham số `-c copy` báo hiệu cho FFmpeg thực hiện **ghép nhị phân dòng dữ liệu trực tiếp (bitstream)**. Do 3 đoạn video được xuất ra cùng thông số codec (h264), fps (24) và độ phân giải (`768x512`), FFmpeg chỉ mất **0.1 giây** trên CPU để khâu chúng lại, hoàn toàn không chạm vào GPU hay thực hiện encode lại từ đầu (re-encoding).

---

## 4. Hướng Dẫn Sử Dụng (How to Use)

### Bước 1: Khởi động ComfyUI Server dưới nền (Nếu chưa bật)
Nếu server bị tắt, bạn có thể chạy câu lệnh sau để bật ComfyUI Server dưới nền:
```bash
/root/comfy_env/bin/python /root/ComfyUI/main.py --port 8188 > /root/comfyui_server.log 2>&1 &
```

### Bước 2: Cấu hình kịch bản video
Mở file [generate_video.py](file:///root/generate_video.py) và tìm đến hàm `main()`. Bạn có thể thay đổi prompt tạo ảnh (Flux) và prompt tạo chuyển động (LTX-Video) cho từng phân đoạn:
```python
    segments = [
        # (Flux Prompt - Ảnh tĩnh, LTX-Video Prompt - Chuyển động, Tên file segment)
        ('A futuristic city at sunset', 'Cinematic drone shot flying through skyscrapers', 'part1.mp4'),
        ('Close up of a robotic eye', 'Mechanical iris opening and glowing neon blue', 'part2.mp4'),
        ('High-tech data center with glowing servers', 'Camera panning down a row of server racks', 'part3.mp4')
    ]
```

### Bước 3: Chạy script sinh video tự động
Kích hoạt script điều phối bằng python:
```bash
/root/comfy_env/bin/python /root/generate_video.py
```
Tiến trình sẽ lần lượt chạy, hiển thị log tiến độ tải/lưu từng phân đoạn và kết thúc bằng thông báo:
`SUCCESS: /root/final_commercial_15s.mp4 generated!`

Tệp video [final_commercial_15s.mp4](file:///root/final_commercial_15s.mp4) dài 15 giây sẽ xuất hiện tại thư mục `/root` của bạn.
