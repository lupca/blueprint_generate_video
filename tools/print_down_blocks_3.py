import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors.bak')
sd = load_file(path)

print("Keys for down_blocks.3:")
for k in sorted(list(sd.keys())):
    if "encoder.down_blocks.3" in k:
        print(f"{k}: {sd[k].shape}")
