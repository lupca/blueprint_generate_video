from huggingface_hub import hf_hub_download
import os

models = [
    ('city96/FLUX.1-schnell-gguf', 'flux1-schnell-Q4_K_S.gguf', 'models/unet'),
    ('city96/LTX-Video-gguf', 'ltx-video-2b-v0.9.1-Q4_K_S.gguf', 'models/unet'),
    ('comfyanonymous/flux_text_encoders', 't5xxl_fp8_e4m3fn.safetensors', 'models/clip'),
    ('comfyanonymous/flux_text_encoders', 'clip_l.safetensors', 'models/clip'),
    ('black-forest-labs/FLUX.1-schnell', 'ae.safetensors', 'models/vae')
]

base_path = os.path.expanduser('~/ComfyUI')

for repo, filename, subfolder in models:
    dest_dir = os.path.join(base_path, subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    print(f'Downloading {filename} from {repo} to {dest_dir}...')
    hf_hub_download(repo_id=repo, filename=filename, local_dir=dest_dir)
