import os

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    lines = f.readlines()

# 1. Extract the LTXV block
ltxv_block = []
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd or "decoder.up_blocks.0.resnets.0.conv1.conv.weight" in sd:' in line:
        start_idx = i
        # Find end of block (next elif or else at same indentation)
        for j in range(i + 1, len(lines)):
            if lines[j].strip().startswith('elif ') or lines[j].strip().startswith('else:'):
                end_idx = j
                break
        break

if start_idx != -1 and end_idx != -1:
    ltxv_block = lines[start_idx:end_idx]
    # Remove it from original position
    del lines[start_idx:end_idx]
    
    # 2. Find the top of 'if config is None:' chain
    top_idx = -1
    for i, line in enumerate(lines):
        if 'if config is None:' in line:
            top_idx = i + 1
            break
            
    if top_idx != -1:
        # Insert LTXV block as the first 'if' (change elif to if)
        ltxv_block[0] = ltxv_block[0].replace('elif ', 'if ')
        # Change the original first 'if' to 'elif'
        lines[top_idx] = lines[top_idx].replace('if ', 'elif ')
        
        # Insert
        for k, l in enumerate(ltxv_block):
            lines.insert(top_idx + k, l)
        
        print('Master Patch: LTXV moved to top')
        with open(path, 'w') as f:
            f.writelines(lines)
    else:
        print('Error: "if config is None:" not found')
else:
    print('Error: LTXV block not found for moving')
