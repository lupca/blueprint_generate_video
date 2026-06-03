# TÀI LIỆU KỸ THUẬT API: COMFYUI HEADLESS AUTOMATION

Tài liệu này hướng dẫn các nhà phát triển (Developers) tích hợp luồng sinh ảnh (Flux.1 Schnell) và sinh video (LTX-Video) của hệ thống này vào bất kỳ dịch vụ backend nào khác (Node.js, Go, Python, Java, v.v.).

Hệ thống hoạt động như một cụm **Silent Server** giao tiếp qua giao thức HTTP REST và WebSockets ở cổng mặc định `8188`. Các file cấu hình đồ thị JSON (`workflow_flux_api.json` và `workflow_ltxv_api.json`) đóng vai trò là cấu trúc điều hướng tham số.

---

## 1. Các Endpoint Cốt Lõi Trên Server ComfyUI

Mọi ứng dụng backend ngoại vi muốn điều phối sinh ảnh/video cần giao tiếp qua 6 endpoint sau:

| Endpoint | Giao thức | Mô tả | Payload/Response |
| :--- | :--- | :--- | :--- |
| `/upload/image` | **POST** | Upload ảnh tĩnh làm ảnh dẫn đường (I2V) | Multipart Form-data $\rightarrow$ Trả về tên file lưu tạm trên server |
| `/prompt` | **POST** | Đệ trình đồ thị JSON để đưa vào hàng đợi xử lý | Application/JSON $\rightarrow$ Trả về `prompt_id` (UUID) |
| `/ws` | **WS** | Mở kết nối WebSocket hai chiều để bắt sự kiện | Nhận luồng tin nhắn JSON cập nhật tiến độ thời gian thực |
| `/history/{id}`| **GET** | Kiểm tra chi tiết lịch sử và kết quả của tác vụ | Trả về thông tin chi tiết các file output sau khi xử lý xong |
| `/view` | **GET** | Tải luồng nhị phân (binary stream) của tệp ảnh/video | Query params `filename`, `subfolder`, `type` $\rightarrow$ Trả về Binary File |
| `/free` | **POST** | Giải phóng GPU VRAM và dọn dẹp cache mô hình | Application/JSON `b"{}"` $\rightarrow$ Trả về trạng thái trống |

---

## 2. Quy Trình Gọi API Từ Dịch Vụ Khác (Developer Integration Flow)

Để phát triển client kết nối, lập trình viên cần triển khai luồng xử lý chuẩn hóa gồm 4 bước:

```
[Dịch vụ của bạn (Client)]                       [ComfyUI Server]
        |                                                |
        |--- 1. (Nếu là I2V) POST /upload/image -------->| (Lưu ảnh tạm)
        |<-- Trả về { "name": "example_upload.png" } ----|
        |                                                |
        |--- 2. Ghép dữ liệu & POST /prompt ------------>| (Thêm vào hàng đợi GPU)
        |<-- Trả về { "prompt_id": "UUID-xxxxx" } -------|
        |                                                |
        |=== 3. Kết nối WebSocket /ws Lắng nghe =========| (GPU xử lý...)
        |<-- Nhận sự kiện {"type":"executing", ...} -----|
        |    (Khi node == null: Tác vụ kết thúc)         |
        |                                                |
        |--- 4. GET /view?filename=... ----------------->| (Tải tệp nhị phân)
        |<-- Nhận Binary Stream (Lưu .png hoặc .mp4) ----|
```

---

## 3. Chi Tiết API 1: Tạo Ảnh Keyframe Tĩnh (Flux.1 Schnell)

Để tạo ảnh, ứng dụng cần nạp tệp `workflow_flux_api.json`, cấu hình prompt và gửi lệnh.

*   **Endpoint đệ trình**: `POST http://127.0.0.1:8188/prompt`
*   **Tham số cần chèn trong JSON**:
    *   Chèn Prompt vào đường dẫn: `workflow["6"]["inputs"]["text"] = "Mô tả bức ảnh của bạn"`
*   **Ví dụ Code (Node.js / Javascript)**:

```javascript
const WebSocket = require('ws');
const axios = require('axios');
const fs = require('fs');

async function generateImage(prompt, outputPath) {
    const server = "127.0.0.1:8188";
    const clientId = "client_uuid_12345";
    
    // 1. Đọc file JSON workflow
    const workflow = JSON.parse(fs.readFileSync('./workflow_flux_api.json', 'utf8'));
    workflow["6"]["inputs"]["text"] = prompt; // Chèn prompt của bạn

    // 2. Mở kết nối WebSocket lắng nghe sự kiện
    const ws = new WebSocket(`ws://${server}/ws?clientId=${clientId}`);
    
    // 3. Submit prompt lên hàng đợi
    const response = await axios.post(`http://${server}/prompt`, {
        prompt: workflow,
        client_id: clientId
    });
    const promptId = response.data.prompt_id;
    console.log(`Đã queue sinh ảnh. Prompt ID: ${promptId}`);

    // 4. Chờ sự kiện Node hoàn tất từ WebSockets
    await new Promise((resolve, reject) => {
        ws.on('message', (data) => {
            const message = JSON.parse(data);
            if (message.type === 'executing') {
                const execData = message.data;
                // node === null báo hiệu toàn bộ workflow đã xử lý xong
                if (execData.node === null && execData.prompt_id === promptId) {
                    ws.close();
                    resolve();
                }
            }
        });
        ws.on('error', reject);
    });

    // 5. Kiểm tra lịch sử để lấy tên file ảnh thực tế
    const historyRes = await axios.get(`http://${server}/history/${promptId}`);
    const outputs = historyRes.data[promptId].outputs;
    
    let filename = "";
    for (const nodeId in outputs) {
        if (outputs[nodeId].images) {
            filename = outputs[nodeId].images[0].filename;
            break;
        }
    }

    // 6. Tải tệp nhị phân của bức ảnh
    const viewRes = await axios.get(`http://${server}/view`, {
        params: { filename: filename, type: "output" },
        responseType: 'stream'
    });
    viewRes.data.pipe(fs.createWriteStream(outputPath));
    console.log(`Tạo ảnh thành công! Đã lưu tại: ${outputPath}`);
}
```

---

## 4. Chi Tiết API 2: Tạo Video (LTX-Video)

API sinh video hỗ trợ cấu hình động: **Text-to-Video (T2V)** hoặc **Image-to-Video (I2V)** tùy thuộc vào việc bạn truyền ảnh dẫn đường hay không.

### 4.1. Bước 1: Upload ảnh tĩnh lên server (Chỉ dùng cho chế độ I2V)
Nếu bạn có ảnh tĩnh từ Flux hoặc ảnh bên ngoài, bạn phải tải nó lên bộ nhớ tạm của ComfyUI trước.

*   **Endpoint**: `POST http://127.0.0.1:8188/upload/image`
*   **Format**: `Multipart Form-Data`
*   **Tham số**:
    *   `image`: File dữ liệu ảnh.
    *   `overwrite`: `true` (boolean)
*   **JSON trả về**:
    ```json
    {
      "name": "example_upload_00001.png",
      "type": "input",
      "subfolder": ""
    }
    ```
    *(Ghi nhớ giá trị trường `name` để đưa vào cấu hình đồ thị ở bước tiếp theo).*

### 4.2. Bước 2: Điền cấu hình đồ thị và Submit `/prompt`
Nạp file `workflow_ltxv_api.json` và điều chỉnh các node đầu vào:

*   **Node "22" (CLIPTextEncode - Positive Prompt)**:
    `workflow["22"]["inputs"]["text"] = "Mô tả hành động chuyển động"`
*   **Node "7" (LTXVImgToVideoAdvanced - Cấu hình mode)**:
    *   Nếu chạy **Text-to-Video (T2V)**:
        `workflow["7"]["inputs"]["bypass_i2v"] = true`
    *   Nếu chạy **Image-to-Video (I2V)**:
        `workflow["7"]["inputs"]["bypass_i2v"] = false`
        `workflow["4"]["inputs"]["image"] = "tên_file_ảnh_ở_bước_1.png"` (Node "4" là LoadImage)

---

## 5. Quy Trình Tự Động Gen Video Dài (>5s) Auto-Regressive

Mô hình LTX-Video chỉ hỗ trợ tạo tối ưu khoảng **5 giây (121 frames)** cho một phân đoạn để tránh méo hình. Để tạo video dài hơn (10s, 15s...), lập trình viên cần triển khai vòng lặp nối tiếp (Auto-regressive) như sau:

1.  **Gen đoạn 1 (`part1.mp4`)**:
    *   Dùng ảnh gốc đầu vào (hoặc T2V nếu không có ảnh) để tạo ra video 5 giây đầu tiên.
2.  **Trích xuất frame cuối của đoạn trước**:
    *   Gọi FFmpeg trích xuất khung hình cuối cùng (chỉ số index frame thứ 120) của tệp video vừa tải về:
        ```bash
        ffmpeg -y -i part1.mp4 -vf "select=eq(n\,120)" -vframes 1 temp_last_frame.png
        ```
3.  **Gen đoạn 2 (`part2.mp4`)**:
    *   Gọi API `/upload/image` tải ảnh `temp_last_frame.png` lên.
    *   Cấu hình chạy **Image-to-Video** với ảnh dẫn đường này $\rightarrow$ ComfyUI sẽ sinh tiếp 5 giây tiếp theo kế thừa hoàn hảo nội dung của đoạn 1.
4.  **Khâu Video bằng FFmpeg Demuxer**:
    *   Ghi danh sách phân đoạn vào tệp `inputs.txt`:
        ```text
        file 'part1.mp4'
        file 'part2.mp4'
        ```
    *   Chạy lệnh khâu nối nhị phân tốc độ cao ngoài GPU (trong 0.1 giây):
        ```bash
        ffmpeg -y -f concat -safe 0 -i inputs.txt -c copy final_video.mp4
        ```

---

## 6. Gọi Giải Phóng GPU VRAM Tức Thời

Sau khi ứng dụng backend hoàn tất việc tải tệp video đầu ra cuối cùng, hãy thực hiện một lệnh gọi POST rỗng đến `/free` để dọn dẹp sạch GPU, đảm bảo các phiên gen sau không bị nghẽn:

*   **Endpoint**: `POST http://127.0.0.1:8188/free`
*   **Headers**: `Content-Type: application/json`
*   **Body**: `b"{}"` (Chuỗi JSON rỗng)
