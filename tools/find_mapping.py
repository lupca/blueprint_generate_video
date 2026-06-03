import sys
import torch
from safetensors.torch import load_file
import os

sys.path.append('/root/ComfyUI')
from comfy.ldm.lightricks.vae.causal_video_autoencoder import VideoVAE

# Load model keys
model = VideoVAE(version=0)
model_keys = sorted(list(model.state_dict().keys()))

# Load checkpoint keys
path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors.bak')
checkpoint_keys = sorted(list(load_file(path).keys()))

print(f"Model keys: {len(model_keys)}")
print(f"Checkpoint keys: {len(checkpoint_keys)}")

# Let's try to map them automatically based on layer types and shapes
# We can print both side-by-side or write a heuristic mapper
with open('/root/mapping_analysis.txt', 'w') as f:
    f.write("MODEL KEYS:\n")
    for k in model_keys:
        f.write(f"{k}\n")
    f.write("\n\nCHECKPOINT KEYS:\n")
    for k in checkpoint_keys:
        f.write(f"{k}\n")

print("Keys written to /root/mapping_analysis.txt")
