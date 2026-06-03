import sys
import os
import torch

sys.path.append('/root/ComfyUI')

from comfy.sd import VAE
from comfy.utils import load_torch_file

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
print("Loading state dict...")
sd = load_torch_file(path)

print("Instantiating VAE...")
try:
    vae = VAE(sd=sd)
    print(f"Instantiated successfully!")
    print(f"first_stage_model type: {type(vae.first_stage_model)}")
except Exception as e:
    print(f"Exception during instantiation: {e}")
    # If it failed, let's catch the exact class if we can
    import traceback
    traceback.print_exc()
