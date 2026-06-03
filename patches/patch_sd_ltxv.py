import os

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    content = f.read()

# Patch 1: Add support for 'resnets' in LTXV detection
old_ltxv = 'elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd:'
new_ltxv = 'elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd or "decoder.up_blocks.0.resnets.0.conv1.conv.weight" in sd:'

if old_ltxv in content:
    content = content.replace(old_ltxv, new_ltxv)
    print('Successfully patched LTXV detection')
else:
    # Try a more generic match if exact string fails
    print('Exact LTXV pattern not found, trying fallback...')
    content = content.replace('elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"', 
                              'elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd or "decoder.up_blocks.0.resnets.0.conv1.conv.weight"')

with open(path, 'w') as f:
    f.write(content)
