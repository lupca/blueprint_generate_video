import sys
import torch
from safetensors.torch import load_file
import os

sys.path.append('/root/ComfyUI')
from comfy.ldm.lightricks.vae.causal_video_autoencoder import VideoVAE

model = VideoVAE(version=0)
model_state = model.state_dict()
model_keys = sorted(list(model_state.keys()))

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors.bak')
checkpoint_state = load_file(path)
checkpoint_keys = sorted(list(checkpoint_state.keys()))

print("Comparing sorted keys:")
mismatches = 0
for idx, (mk, ck) in enumerate(zip(model_keys, checkpoint_keys)):
    ms = model_state[mk].shape
    cs = checkpoint_state[ck].shape
    if ms != cs:
        print(f"Mismatch at {idx}:")
        print(f"  Model:      {mk} -> {ms}")
        print(f"  Checkpoint: {ck} -> {cs}")
        mismatches += 1

if mismatches == 0:
    print("All sorted keys match in shape perfectly!")
else:
    print(f"Total mismatches: {mismatches}")
