import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors.bak')
sd = load_file(path)

print("Encoder non-down_blocks keys:")
for k in sorted(list(sd.keys())):
    if "encoder." in k and "down_blocks" not in k:
        print(f"{k}: {sd[k].shape}")
