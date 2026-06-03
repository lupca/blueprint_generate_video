import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
sd = load_file(path)

print(f"'post_quant_conv.weight' in sd: {'post_quant_conv.weight' in sd}")
