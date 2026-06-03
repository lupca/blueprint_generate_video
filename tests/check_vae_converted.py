import torch
from safetensors.torch import load_file
import os
import sys

# Add ComfyUI to path to import diffusers_convert
sys.path.append('/root/ComfyUI')
from comfy import diffusers_convert

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
try:
    sd = load_file(path)
    print(f"Original keys count: {len(sd)}")
    
    # Simulate ComfyUI conversion
    if 'decoder.up_blocks.0.resnets.0.norm1.weight' in sd.keys():
        print("Diffusers format detected, converting...")
        sd = diffusers_convert.convert_vae_state_dict(sd)
        print(f"Converted keys count: {len(sd)}")
    
    print("Top 20 keys after conversion:")
    print(sorted(list(sd.keys()))[:20])
    
    target_key = "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"
    print(f"Is '{target_key}' in converted sd? {target_key in sd}")
    
    # Search for anything similar
    similar = [k for k in sd.keys() if "up_blocks.0" in k and "conv1" in k]
    print("Similar keys found:")
    print(similar[:5])

except Exception as e:
    print(f"Error: {e}")
