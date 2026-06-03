import torch
from safetensors.torch import load_file
import os
import sys

sys.path.append('/root/ComfyUI')
from comfy import diffusers_convert

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
try:
    sd = load_file(path)
    
    # Check if conversion would trigger
    if 'decoder.up_blocks.0.resnets.0.norm1.weight' in sd.keys():
        print("Conversion WILL trigger in ComfyUI.")
        sd = diffusers_convert.convert_vae_state_dict(sd)
    else:
        print("Conversion will NOT trigger in ComfyUI.")
    
    print(f"Total keys: {len(sd)}")
    print("All keys (first 100):")
    for k in sorted(list(sd.keys()))[:100]:
        print(k)

except Exception as e:
    print(f"Error: {e}")
