import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/flux_vae.safetensors')
try:
    sd = load_file(path)
    print(f"'post_quant_conv.weight' in sd: {'post_quant_conv.weight' in sd}")
    print(f"'encoder.conv_in.weight' in sd: {'encoder.conv_in.weight' in sd}")
    if 'encoder.conv_in.weight' in sd:
        print(f"Shape: {sd['encoder.conv_in.weight'].shape}")
    print("First 20 keys:")
    print(sorted(list(sd.keys()))[:20])
except Exception as e:
    print(f"Error: {e}")
