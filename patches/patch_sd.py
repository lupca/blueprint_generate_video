import os
import torch

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    lines = f.readlines()

patched = False
with open(path, 'w') as f:
    for line in lines:
        if "sd['post_quant_conv.weight'].shape[1]" in line:
            new_line = line.replace("sd['post_quant_conv.weight'].shape[1]", "sd.get('post_quant_conv.weight', torch.zeros(1, 16)).shape[1]")
            f.write(new_line)
            patched = True
        else:
            f.write(line)

if patched:
    print('Successfully patched sd.py')
else:
    print('Pattern not found in sd.py')
