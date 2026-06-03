import os

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    lines = f.readlines()

# 1. Reconstruct the full LTXV block
ltxv_full_block = [
    '            if "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd or "decoder.up_blocks.0.resnets.0.conv1.conv.weight" in sd: #lightricks ltxv\n',
    '                if "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd:\n',
    '                    tensor_conv1 = sd["decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"]\n',
    '                else:\n',
    '                    tensor_conv1 = sd["decoder.up_blocks.0.resnets.0.conv1.conv.weight"]\n',
    '                version = 0\n',
    '                if tensor_conv1.shape[0] == 512:\n',
    '                    version = 0\n',
    '                elif tensor_conv1.shape[0] == 1024:\n',
    '                    version = 1\n',
    '                    if "encoder.down_blocks.1.conv.conv.bias" in sd:\n',
    '                        version = 2\n',
    '                vae_config = None\n',
    '                if metadata is not None and "config" in metadata:\n',
    '                    vae_config = json.loads(metadata["config"]).get("vae", None)\n',
    '                self.first_stage_model = comfy.ldm.lightricks.vae.causal_video_autoencoder.VideoVAE(version=version, config=vae_config)\n',
    '                self.latent_channels = 128\n',
    '                self.latent_dim = 3\n',
    '                self.memory_used_decode = lambda shape, dtype: (1200 * shape[2] * shape[3] * shape[4] * (8 * 8 * 8)) * model_management.dtype_size(dtype)\n',
    '                self.memory_used_encode = lambda shape, dtype: (80 * max(shape[2], 7) * shape[3] * shape[4]) * model_management.dtype_size(dtype)\n',
    '                self.upscale_ratio = (lambda a: max(0, a * 8 - 7), 32, 32)\n',
    '                self.upscale_index_formula = (8, 32, 32)\n',
    '                self.downscale_ratio = (lambda a: max(0, math.floor((a + 7) / 8)), 32, 32)\n',
    '                self.downscale_index_formula = (8, 32, 32)\n',
    '                self.working_dtypes = [torch.bfloat16, torch.float32]\n'
]

# 2. Find the current (broken) LTXV block and remove it
new_lines = []
skip = False
for line in lines:
    if '#lightricks ltxv' in line:
        skip = True
        continue
    if skip and (line.strip().startswith('elif ') or line.strip().startswith('else:')):
        skip = False
    
    if not skip:
        new_lines.append(line)

# 3. Find the top of 'if config is None:' chain
top_idx = -1
for i, line in enumerate(new_lines):
    if 'if config is None:' in line:
        top_idx = i + 1
        break

if top_idx != -1:
    # Ensure the NEXT line is an 'elif' if it was an 'if'
    if new_lines[top_idx].strip().startswith('if '):
        new_lines[top_idx] = new_lines[top_idx].replace('if ', 'elif ')
    
    # Insert full block
    for k, l in enumerate(ltxv_full_block):
        new_lines.insert(top_idx + k, l)
    
    with open(path, 'w') as f:
        f.writelines(new_lines)
    print('Full Reconstruction Successful: LTXV restored and moved to top')
else:
    print('Error: "if config is None:" not found')
