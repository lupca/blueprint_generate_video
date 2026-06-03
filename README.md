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
Ảnh đầu ra (`IMAGE`) từ node **VAE Decode** của mô hình Flux được đấu trực tiếp vào cổng đầu vào `image` của node **LTXVImgToVideoAdvanced**. Điều này giúp dữ liệu truyền trực tiếp trong bộ nhớ VRAM của GPU:
*   `Flux VAE Decode (IMAGE)` -> `LTXVImgToVideoAdvanced (image)`.

---

## 2. Giao Thức API & Cơ Chế Hoạt Động (Headless Automation & WebSockets)

Quá trình điều phối chạy độc lập qua script Python thông qua các endpoint nội bộ của ComfyUI (`127.0.0.1:8188`):

1.  **Khởi tạo kết nối song phương (`/ws`)**:
    Script mở một kết nối WebSocket nối dài đến máy chủ: `ws://127.0.0.1:8188/ws?clientId={UUID}`.
2.  **Đệ trình tác vụ (`/prompt`)**:
    Script điền văn bản kịch bản (prompt) vào node `"6"` (Flux) và node `"22"` (LTX-Video) của `workflow_api.json`, gửi yêu cầu HTTP POST đến `/prompt` và nhận về `prompt_id` (UUID tác vụ).
3.  **Lắng nghe sự kiện (Event Interception)**:
    Client liên tục đọc gói tin từ WebSocket. Khi nhận được gói tin báo hiệu kết thúc (`node` là `null` khớp với `prompt_id`), client sẽ dừng vòng lặp chờ.
4.  **Xử lý Ngoại lệ / Timeout Fallback**:
    Để chống treo luồng khi mất kết nối mạng, script cài đặt timeout **5 phút** cho mỗi segment. Nếu hết thời gian hoặc mất kết nối, hệ thống tự động chuyển sang cơ chế **Polling**. Client sẽ gửi lệnh HTTP GET đến endpoint `/history/{prompt_id}` mỗi 5 giây để kiểm tra xem tác vụ đã hoàn thành trên server hay chưa.
5.  **Tải Video nhị phân (`/view`)**:
    Khi lịch sử xác nhận hoàn tất, client gửi HTTP GET đến `/view?filename=...` để kéo dòng dữ liệu nhị phân về lưu trữ cục bộ thành `part1.mp4`, `part2.mp4`, `part3.mp4`.

---

## 3. Khâu Hậu Kỳ Thần Tốc (FFmpeg Concat)

Sau khi có đủ 3 video ngắn 5 giây, script tự động ghi danh sách tệp vào `inputs.txt` và gọi FFmpeg ghép chúng lại bằng thuật toán **Concat Demuxer**:
```bash
ffmpeg -y -f concat -safe 0 -i inputs.txt -c copy final_commercial_15s.mp4
```
Tham số `-c copy` thực hiện **ghép nhị phân dòng dữ liệu trực tiếp (bitstream)**. FFmpeg chỉ mất **0.1 giây** trên CPU để khâu chúng lại, hoàn toàn không tiêu tốn tài nguyên GPU hay thực hiện mã hóa lại từ đầu.

---

## 4. Hướng Dẫn Sử Dụng (How to Use)

1.  **Bật ComfyUI Server dưới nền (nếu chưa bật)**:
    ```bash
    /root/comfy_env/bin/python /root/ComfyUI/main.py --port 8188 > /root/comfyui_server.log 2>&1 &
    ```
2.  **Cấu hình kịch bản video**: Sửa danh sách prompt của 3 phân đoạn trong hàm `main()` của file [generate_video.py](file:///root/generate_video.py).
3.  **Chạy script sinh video**:
    ```bash
    /root/comfy_env/bin/python /root/generate_video.py
    ```
    Video hoàn chỉnh [final_commercial_15s.mp4](file:///root/final_commercial_15s.mp4) sẽ được tạo ra tại thư mục gốc.

---

## 5. Hướng Dẫn Cài Đặt Lại & Triển Khai Trên Máy Chủ Mới

Khi di chuyển sang một máy chủ mới, hãy thực hiện theo các bước sau để thiết lập môi trường:

### Bước 5.1: Cài đặt ComfyUI & Custom Nodes
1.  Tạo môi trường ảo Python và cài đặt PyTorch phù hợp với CUDA:
    ```bash
    python3 -m venv comfy_env
    source comfy_env/bin/activate
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    pip install websocket-client
    ```
2.  Clone mã nguồn ComfyUI gốc:
    ```bash
    git clone https://github.com/comfyanonymous/ComfyUI.git
    cd ComfyUI
    pip install -r requirements.txt
    ```
3.  Cài đặt 3 Custom Nodes chính thức từ GitHub vào thư mục `ComfyUI/custom_nodes`:
    ```bash
    cd custom_nodes
    git clone https://github.com/city96/ComfyUI-GGUF.git
    git clone https://github.com/lightricks/ComfyUI-LTXVideo.git
    git clone https://github.com/kosinkadink/ComfyUI-VideoHelperSuite.git
    ```
    *(Cài đặt dependencies cho từng custom node nếu có yêu cầu)*.

### Bước 5.2: Tải Mô Hình & Text Encoders
Tải các tệp mô hình sau từ Hugging Face về đặt vào các đường dẫn tương ứng:
*   **Flux UNET GGUF**: `flux1-schnell-Q4_K_S.gguf` đặt vào `ComfyUI/models/unet/`
*   **LTX-Video UNET GGUF**: `ltx-video-2b-v0.9-Q4_K_S.gguf` đặt vào `ComfyUI/models/unet/`
*   **Flux VAE**: `flux_vae.safetensors` đặt vào `ComfyUI/models/vae/`
*   **Text Encoders**: `clip_l.safetensors` và `t5xxl_fp8_e4m3fn.safetensors` đặt vào `ComfyUI/models/clip/` (hoặc `text_encoders/`)

### Bước 5.3: Chuyển Đổi VAE LTX-Video
Tải tệp VAE gốc `ltx_video_vae.safetensors` (Diffusers format) về thư mục `ComfyUI/models/vae/`. Chạy tệp script chuyển đổi key-mapping để sinh bản tương thích bản địa cho ComfyUI:
```bash
python /root/convert_vae_to_comfy.py
```
*(Lệnh này sẽ đọc `ltx_video_vae.safetensors` gốc, ánh xạ lại 190 khóa sang dạng native phẳng và ghi đè lại chính nó)*.

---

## 6. Hướng Dẫn Git & SSH

Thư mục `/root` đã được khởi tạo sẵn git cục bộ với bộ lọc `.gitignore` nghiêm ngặt để chỉ theo dõi mã nguồn tùy chỉnh và tài liệu hướng dẫn của bạn.

### Các tệp được Git theo dõi (Whitelisted):
*   `.gitignore`
*   `README.md`
*   `generate_video.py`
*   `workflow_api.json`
*   `convert_vae_to_comfy.py`

*(Tất cả các thư mục mô hình lớn, môi trường ảo Python `comfy_env`, mã nguồn của `ComfyUI`, tệp log và video đầu ra đều bị bỏ qua tự động)*.

### Cách đưa code lên Repository của bạn:

1.  **Sao chép SSH Public Key**:
    Copy toàn bộ chuỗi ký tự trong file SSH công khai đã tạo tại máy chủ này: `/root/.ssh/id_ed25519.pub`. Thêm nó vào cài đặt SSH Keys trên tài khoản GitHub/GitLab của bạn.
2.  **Liên kết Repository từ xa**:
    ```bash
    git remote add origin git@github.com:USER/YOUR-REPO.git
    ```
3.  **Push code lên**:
    ```bash
    git push -u origin master
    ```
