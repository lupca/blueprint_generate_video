import torch
from safetensors.torch import load_file
import os
import sys

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
sd = load_file(path)

print("Starting simulation...")
if "encoder.conv_in.conv.weight" in sd:
    print("Key exists!")
    shape = sd["encoder.conv_in.conv.weight"].shape
    print(f"Shape: {shape}")
    if shape[1] == 48:
        print("shape[1] == 48 is True!")
    else:
        print("shape[1] == 48 is False!")
else:
    print("Key does not exist!")

print("Checking the exact condition string from sd.py:")
cond = "encoder.conv_in.conv.weight" in sd and sd["encoder.conv_in.conv.weight"].shape[1] == 48
print(f"Condition result: {cond}")

# Let's also check if there is an issue with config
config = None
if config is None:
    print("config is None is True")
