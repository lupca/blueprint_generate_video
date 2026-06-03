import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
try:
    sd = load_file(path)
    print(f'encoder.conv_in.conv.weight in sd: {"encoder.conv_in.conv.weight" in sd}')
    if "encoder.conv_in.conv.weight" in sd:
        print(f'Shape: {sd["encoder.conv_in.conv.weight"].shape}')
    else:
        print('Keys (first 20):')
        print(list(sd.keys())[:20])
except Exception as e:
    print(f'Error reading VAE: {e}')
