import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors.bak')
sd = load_file(path)

print(f"Original VAE keys count: {len(sd)}")
print("First 20 keys:")
print(sorted(list(sd.keys()))[:20])
