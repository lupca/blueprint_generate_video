import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
sd = load_file(path)

key = "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"
if key in sd:
    print(f"{key} shape: {sd[key].shape}")
else:
    print(f"{key} NOT in sd!")
