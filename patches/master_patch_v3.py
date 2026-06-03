import os
import re

path = '/root/ComfyUI/comfy/sd.py'
with open(path, 'r') as f:
    content = f.read()

# 1. Clean the mess: remove everything from the start of __init__ detection to the first known stable elif
# We'll target the block from 'if config is None:' to 'elif "decoder.mid.block_1.mix_factor" in sd:'

new_ltxv_block = '''        if config is None:
            if "encoder.conv_in.conv.weight" in sd and sd["encoder.conv_in.conv.weight"].shape[1] == 48: # LTXV detected by 48 channels
                if "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd:
                    tensor_conv1 = sd["decoder.up_blocks.0.res_blocks.0.conv1.conv.weight"]
                else:
                    tensor_conv1 = sd["decoder.up_blocks.0.resnets.0.conv1.conv.weight"]
                version = 0
                if tensor_conv1.shape[0] == 512:
                    version = 0
                elif tensor_conv1.shape[0] == 1024:
                    version = 1
                    if "encoder.down_blocks.1.conv.conv.bias" in sd:
                        version = 2
                vae_config = None
                if metadata is not None and "config" in metadata:
                    vae_config = json.loads(metadata["config"]).get("vae", None)
                self.first_stage_model = comfy.ldm.lightricks.vae.causal_video_autoencoder.VideoVAE(version=version, config=vae_config)
                self.latent_channels = 128
                self.latent_dim = 3
                self.memory_used_decode = lambda shape, dtype: (1200 * shape[2] * shape[3] * shape[4] * (8 * 8 * 8)) * model_management.dtype_size(dtype)
                self.memory_used_encode = lambda shape, dtype: (80 * max(shape[2], 7) * shape[3] * shape[4]) * model_management.dtype_size(dtype)
                self.upscale_ratio = (lambda a: max(0, a * 8 - 7), 32, 32)
                self.upscale_index_formula = (8, 32, 32)
                self.downscale_ratio = (lambda a: max(0, math.floor((a + 7) / 8)), 32, 32)
                self.downscale_index_formula = (8, 32, 32)
                self.working_dtypes = [torch.bfloat16, torch.float32]
            elif "decoder.mid.block_1.mix_factor" in sd:'''

# Use regex to replace the potentially duplicated/messy start of the chain
# We search for the pattern starting from 'if config is None:' and ending at the first stable 'elif'
content = re.sub(r'if config is None:.*?elif "decoder.mid.block_1.mix_factor" in sd:', new_ltxv_block, content, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(content)
print('Master Patch V3: Surgical cleanup and restoration successful')
