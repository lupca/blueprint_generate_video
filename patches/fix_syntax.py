import os

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    content = f.read()

# Fix the syntax error: The previous block ended, but the next block starts with 'elif'
# Let's replace that specific 'elif' with an 'if' because it's inside 'if config is None:'

broken_str = '            elif "decoder.mid.block_1.mix_factor" in sd:'
fixed_str = '            if "decoder.mid.block_1.mix_factor" in sd:'

if broken_str in content:
    content = content.replace(broken_str, fixed_str, 1) # Replace only the first instance
    with open(path, 'w') as f:
        f.write(content)
    print('Syntax fixed successfully.')
else:
    print('Syntax error string not found.')
