import os
import re

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    content = f.read()

debug_code = '''        print(f"DEBUG VAE INIT: Keys count: {len(sd.keys())}")
        if "encoder.conv_in.conv.weight" in sd:
            print(f"DEBUG VAE INIT: encoder.conv_in.conv.weight shape: {sd['encoder.conv_in.conv.weight'].shape}")
        else:
            print("DEBUG VAE INIT: encoder.conv_in.conv.weight NOT FOUND!")

        if config is None:'''

content = content.replace('        if config is None:', debug_code, 1)

with open(path, 'w') as f:
    f.write(content)
print("Debug injection successful.")
