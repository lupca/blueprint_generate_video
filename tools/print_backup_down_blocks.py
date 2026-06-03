import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors.bak')
sd = load_file(path)

print("Encoder down_blocks keys in backup file (first 50):")
keys = [k for k in sd.keys() if "encoder.down_blocks" in k]
for k in sorted(keys)[:50]:
    print(f"{k}: {sd[k].shape}")
