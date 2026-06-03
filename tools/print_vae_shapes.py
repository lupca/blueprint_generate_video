import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
sd = load_file(path)

print("Printing some key shapes to detect LTXV version:")
for k in sorted(list(sd.keys())):
    if "down_blocks" in k and "conv1.conv.weight" in k:
        print(f"{k}: {sd[k].shape}")
