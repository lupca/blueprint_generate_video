import os

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd or "decoder.up_blocks.0.resnets.0.conv1.conv.weight" in sd:' in line:
        new_lines.append(line)
        i += 1
        next_line = lines[i]
        if 'tensor_conv1 = sd["decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"]' in next_line:
            new_lines.append('                if "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd:\n')
            new_lines.append('                    tensor_conv1 = sd["decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"]\n')
            new_lines.append('                else:\n')
            new_lines.append('                    tensor_conv1 = sd["decoder.up_blocks.0.resnets.0.conv1.conv.weight"]\n')
            print('Patched LTXV block body')
        else:
            new_lines.append(next_line)
    else:
        new_lines.append(line)
    i += 1

with open(path, 'w') as f:
    f.writelines(new_lines)
