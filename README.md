# Hướng Dẫn Sử Dụng & Kiến Trúc Hệ Thống Gen Video Tự Động (Decoupled APIs)

Hệ thống đã được tái cấu trúc thành **2 API độc lập hoàn toàn**:
1.  **API Tạo Ảnh (`generate_image.py`)**: Tạo ảnh tĩnh keyframe bằng mô hình **Flux.1 Schnell (GGUF)**.
2.  **API Tạo Video (`generate_video.py`)**: Sinh video chuyển động bằng mô hình **LTX-Video 0.9.8 Distilled (GGUF)**. Hỗ trợ cả chế độ **Text-to-Video (T2V)** lẫn **Image-to-Video (I2V)**, tùy chỉnh thời lượng (5s, 10s, 15s...), tự động kết nối khung hình liên tục (auto-regressive) và khâu video bằng FFmpeg.

---

## 0. Khởi chạy Server ComfyUI (Bắt buộc)

Trước khi chạy các script API, bạn cần đảm bảo server ComfyUI đang hoạt động:
```bash
/root/comfy_env/bin/python /root/ComfyUI/main.py --listen 127.0.0.1 --port 8188
```

---

## 1. API 1: Tạo Ảnh Keyframe Tĩnh (Flux.1 Schnell)

API này kích hoạt mô hình Flux để vẽ ra một bức ảnh tĩnh chất lượng cao từ mô tả văn bản.

### Cú pháp chạy:
```bash
/root/comfy_env/bin/python /root/scripts/generate_image.py --prompt "MÔ_TẢ_BỨC_ẢNH" --output "TÊN_FILE_ẢNH_ĐẦU_RA.png"
```

### Ví dụ:
```bash
/root/comfy_env/bin/python /root/scripts/generate_image.py --prompt "A futuristic cybernetic tiger with glowing neon blue stripes, photorealistic, 8k resolution" --output "tiger_keyframe.png"
```
*Tệp ảnh `tiger_keyframe.png` sẽ được lưu trực tiếp tại thư mục chạy của bạn.*

---

## 2. API 2: Tạo Video Chuyên Nghiệp (LTX-Video)

API này vận hành độc lập để tạo ra video. Bạn có thể gen video thuần từ mô tả văn bản (Text-to-Video) hoặc tạo chuyển động kế thừa từ một bức ảnh tĩnh có sẵn (Image-to-Video).

### Cú pháp chạy:
```bash
/root/comfy_env/bin/python /root/scripts/generate_video.py \
  --prompt "MÔ_TẢ_CHUYỂN_ĐỘNG" \
  [--image "ĐƯỜNG_DẪN_ẢNH_TĨNH"] \
  [--duration THỜI_GIAN_GIÂY] \
  [--output "TÊN_VIDEO_ĐẦU_RA.mp4"]
```

### Các tham số:
*   `--prompt` (Bắt buộc): Mô tả chuyển động của video (ví dụ: góc quay camera di chuyển thế nào, hành động của vật thể).
*   `--image` (Tùy chọn): Đường dẫn ảnh tĩnh để chạy chế độ **Image-to-Video (I2V)**. Nếu không truyền tham số này, API sẽ tự động chuyển sang chế độ **Text-to-Video (T2V)** thuần túy.
*   `--duration` (Tùy chọn, mặc định là 5): Độ dài video bằng giây (nhập các bội số của 5 như 5, 10, 15, 20...).
*   `--output` (Tùy chọn, mặc định là `final_output.mp4`): Tên file video kết quả xuất ra.

---

## 3. Các Ví Dụ Thực Tế Chạy Video (Giống Hệt Hệ Thống Lớn)

### Ví dụ 3.1: Tạo Video Thuần từ Văn Bản (Text-to-Video - T2V) - Dài 10 giây
Tạo video dài 10 giây di chuyển qua thành phố tương lai mà không cần ảnh đầu vào:
```bash
/root/comfy_env/bin/python /root/scripts/generate_video.py \
  --prompt "Cinematic drone shot flying through skyscrapers in a futuristic city at sunset, 4k" \
  --duration 10 \
  --output "city_10s.mp4"
```

### Ví dụ 3.2: Tạo Video Kế Thừa từ Ảnh (Image-to-Video - I2V) - Dài 15 giây
Sinh chuyển động dài 15 giây lấy ảnh `tiger_keyframe.png` (đã gen từ Flux ở bước 1) làm khung hình xuất phát:
```bash
/root/comfy_env/bin/python /root/scripts/generate_video.py \
  --prompt "The robotic tiger slowly walks forward, roaring majestically with sparks flying around, glowing neon lines" \
  --image "tiger_keyframe.png" \
  --duration 15 \
  --output "tiger_commercial_15s.mp4"
```

---

## 4. Cơ Chế Hoạt Động Auto-Regressive Nối Tiếp Dài Giây

Để tạo ra các video dài hơn 5 giây (ví dụ: 15 giây) mà vẫn đảm bảo tính **nhất quán logic nội dung** giữa các phân đoạn, hệ thống tự động thực hiện quy trình sau dưới nền:

```
[Ảnh Đầu Vào / T2V] -> [Gen Phân Đoạn 1 (5s)] -> [Lưu part1.mp4]
                                                       |
                                                       v (Trích xuất Khung hình CUỐI của part1.mp4)
                                                 [temp_last_frame.png]
                                                       |
                                                       v (Dùng làm Ảnh Đầu Vào cho Phân Đoạn 2)
                                                [Gen Phân Đoạn 2 (5s)] -> [Lưu part2.mp4]
                                                                               |
                                                                               v (Trích xuất Khung hình CUỐI)
                                                                         [Gen Phân Đoạn 3 (5s)] -> [Lưu part3.mp4]
                                                                                                        |
[Video 15s Hoàn Chỉnh] <-- [Ghép bitstream qua FFmpeg Demuxer] <-----------------------------------------+
```

1.  **Trích xuất Khung hình Cuối**: Hệ thống dùng FFmpeg cắt chính xác frame thứ 120 (khung hình cuối cùng của giây thứ 5) của đoạn trước đó lưu tạm thành `temp_last_frame.png`.
2.  **Kế thừa Tự Động**: Tải khung hình cuối này lên server ComfyUI làm ảnh dẫn đường (I2V) cho phân đoạn tiếp theo.
3.  **Khâu Nhị Phân Ngoài GPU**: FFmpeg Demuxer tự động khâu nối các phân đoạn nhị phân (`part1.mp4`, `part2.mp4`...) thành một video đồng nhất chỉ trong **0.1 giây**, không làm nặng bộ nhớ GPU và giữ nguyên chất lượng gốc.
4.  **Giải phóng GPU tự động**: Sau khi hoàn tất tất cả các phân đoạn, API tự động gọi lệnh `/free` để ép giải phóng toàn bộ VRAM bộ nhớ đồ họa.
