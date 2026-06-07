# Walkthrough: ComfyUI Server Deployment and Client Integration

We have successfully migrated the ComfyUI backend from a local Windows environment to an Ubuntu Server dockerized container, and integrated it with both `blueprint_generate_video` and `marketing-video-agent`. Additionally, we optimized the LTX-Video workflow to fully utilize the RTX 4060 Ti 16GB VRAM, enhancing quality and resolving precision issues.

## Changes Made

### 1. File Copying
* Copied 17GB of model weights, VAEs, custom nodes, and inputs from the shared HDD directory `/hdd-data/ComfyUI-Shared/` to the NVMe SSD directory `/data/comfyui/` via `rsync`.

### 2. Host Configuration (NVIDIA Container Toolkit)
* Configured the APT repository for the NVIDIA Container Toolkit.
* Installed the `nvidia-container-toolkit` package.
* Configured Docker daemon configuration (`/etc/docker/daemon.json`) to register the NVIDIA runtime and restarted the Docker service.

### 3. Docker Compose Setup
* Created the file [docker-compose.comfyui.yml](../docker-compose.comfyui.yml) to deploy the `yanwk/comfyui-boot:cu128-slim` container with full GPU capability.
* Mounted `/data/comfyui` subdirectories for models, custom nodes, inputs, and outputs.
* Launched the container successfully using the host GPU (`RTX 4060 Ti 16GB`).

### 4. Client Script Updates
* Modified [generate_image.py](../scripts/generate_image.py#L10-L15) and [generate_video.py](../scripts/generate_video.py#L10-L17) to:
  * Read the ComfyUI host address via the `COMFYUI_SERVER_ADDRESS` environment variable, falling back to `localhost:8188`.
  * Automatically strip any `http://` or `https://` prefix from the variable to maintain WebSocket and raw connection compatibility.
  * Dynamically resolve `base_dir` in `generate_video.py` relative to the script's path rather than using a hardcoded `/root/blueprint_generate_video` directory.

### 5. Agent Integration
* Added the `COMFYUI_URL=http://localhost:8188` environment variable to the `marketing-video-agent` [.env](../../marketing-video-agent/.env#L9) configuration file, enabling Celery workers to communicate with the new container.

### 6. LTX-Video 16GB VRAM Optimization
* **Model Configuration**: Configured the workflow to use the high-fidelity base model `ltx-video-2b-v0.9-Q8_0.gguf` to avoid "pig mode" compatibility bugs and severe noise associated with distilled models.
* **VAE Precision Fix**: Configured the VAE Decode node (`LTXVSpatioTemporalTiledVAEDecode`, Node 12) `"working_dtype"` to `"float32"` to completely prevent VAE calculation overflow (fixing neon color artifacts and posterization).
* **AI Upscaler Integration**: Replaced standard bicubic interpolation with high-fidelity `4x-UltraSharp` upscaling (via `UpscaleModelLoader` and `ImageUpscaleWithModel`) followed by a clean `lanczos` downscaling to target dimensions, feeding seamlessly into the RIFE interpolator.
* **Image-to-Video Mode**: Validated the Image-to-Video pipeline utilizing `--image test_gen_image.png` (using text-to-video with empty latent at 30 steps can result in NaN collapses/black frames, whereas image conditioning is highly stable and realistic).

### 7. Version Control
* Committed the optimized workflow and Python script paths and successfully pushed them to GitHub (`origin/master`).

---

## Verification Results

### 1. ComfyUI Server Health check
* The server launched successfully and loaded all custom nodes:
  * `ComfyUI-Frame-Interpolation`
  * `ComfyUI-GGUF`
  * `ComfyUI-LTXVideo`
  * `ComfyUI-VideoHelperSuite`
* Server responsiveness tested and confirmed:
  ```bash
  curl -I http://localhost:8188
  # HTTP/1.1 200 OK
  ```

### 2. End-to-End Image Generation
* Running `generate_image.py` generated and saved the keyframe successfully:
  ```bash
  ./venv/bin/python3 scripts/generate_image.py --prompt "a beautiful photo of a futuristic cat" --output test_gen_image.png
  # SUCCESS: Image saved to /data/projects/blueprint_generate_video/test_gen_image.png
  ```

### 3. End-to-End Optimized Video Generation (I2V)
* Running `generate_video.py` using the updated workflow JSON with image conditioning:
  ```bash
  ./venv/bin/python3 scripts/generate_video.py \
    --prompt "The cat blinks, slowly looks around, hyper-detailed, photorealistic motion." \
    --image test_gen_image.png \
    --duration 5 \
    --output test_distilled_gen.mp4
  # SUCCESS: /data/projects/blueprint_generate_video/test_distilled_gen.mp4 generated successfully!
  ```
* Visual check confirmed:
  * Zero neon color interference (VAE precision fix successful).
  * Smooth, high-quality, and artifact-free generation with the Q8 base model.
  * Stable ~12.5GB GPU VRAM usage during upscaling and RIFE operations (no out-of-memory).
