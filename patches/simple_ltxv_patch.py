import os

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    content = f.read()

original_if = 'elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd: #lightricks ltxv'
new_if = 'elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd or "decoder.up_blocks.0.resnets.0.conv1.conv.weight" in sd: #lightricks ltxv'

original_tensor = 'tensor_conv1 = sd["decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"]'
new_tensor = 'tensor_conv1 = sd.get("decoder.up_blocks.0.res_blocks.0.conv1.conv.weight", sd.get("decoder.up_blocks.0.resnets.0.conv1.conv.weight"))'

if original_if in content:
    content = content.replace(original_if, new_if)
    content = content.replace(original_tensor, new_tensor)
    with open(path, 'w') as f:
        f.write(content)
    print("Simple LTXV Patch Applied Successfully!")
else:
    print("Failed to find original string!")
