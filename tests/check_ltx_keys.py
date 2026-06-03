import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
try:
    sd = load_file(path)
    key = "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"
    print(f"{key} in sd: {key in sd}")
    if key not in sd:
        print("First 50 keys:")
        print(sorted(list(sd.keys()))[:50])
except Exception as e:
    print(f"Error: {e}")
