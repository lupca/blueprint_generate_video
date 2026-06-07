import torch
from safetensors.torch import load_file, save_file
import os

src_path = os.path.expanduser('/data/comfyui/models/vae/ltx_video_vae.safetensors.bak')
dst_path = os.path.expanduser('/data/comfyui/models/vae/ltx_video_vae.safetensors')

sd = load_file(src_path)
new_sd = {}

mapped_count = 0

for k, v in sd.items():
    new_k = k
    
    # 1. Global / direct matches
    if k.startswith("encoder.conv_in."):
        new_k = k
    elif k.startswith("encoder.conv_out."):
        new_k = k
    elif k.startswith("decoder.conv_in."):
        new_k = k
    elif k.startswith("decoder.conv_out."):
        new_k = k
    elif k.startswith("decoder.conv_norm_out."):
        new_k = k
    elif k == "latents_mean":
        new_k = "per_channel_statistics.mean-of-means"
    elif k == "latents_std":
        new_k = "per_channel_statistics.std-of-means"
        
    # 2. Encoder mapping
    elif k.startswith("encoder.down_blocks."):
        parts = k.split('.')
        block_idx = int(parts[2])
        last_part = parts[-1]
        
        if block_idx == 0:
            if parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"encoder.down_blocks.0.res_blocks.{layer_idx}.{rest}"
            elif parts[3] == "downsamplers":
                new_k = f"encoder.down_blocks.1.conv.{last_part}"
            elif parts[3] == "conv_out":
                if "conv_shortcut" in parts:
                    new_k = f"encoder.down_blocks.2.conv_shortcut.{last_part}"
                elif "norm3" in parts:
                    new_k = f"encoder.down_blocks.2.norm3.norm.{last_part}"
                else:
                    rest = '.'.join(parts[4:])
                    new_k = f"encoder.down_blocks.2.{rest}"
                
        elif block_idx == 1:
            if parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"encoder.down_blocks.3.res_blocks.{layer_idx}.{rest}"
            elif parts[3] == "downsamplers":
                new_k = f"encoder.down_blocks.4.conv.{last_part}"
            elif parts[3] == "conv_out":
                if "conv_shortcut" in parts:
                    new_k = f"encoder.down_blocks.5.conv_shortcut.{last_part}"
                elif "norm3" in parts:
                    new_k = f"encoder.down_blocks.5.norm3.norm.{last_part}"
                else:
                    rest = '.'.join(parts[4:])
                    new_k = f"encoder.down_blocks.5.{rest}"
                
        elif block_idx == 2:
            if parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"encoder.down_blocks.6.res_blocks.{layer_idx}.{rest}"
            elif parts[3] == "downsamplers":
                new_k = f"encoder.down_blocks.7.conv.{last_part}"
                
        elif block_idx == 3:
            if parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"encoder.down_blocks.8.res_blocks.{layer_idx}.{rest}"
                
    elif k.startswith("encoder.mid_block."):
        parts = k.split('.')
        if parts[2] == "resnets":
            layer_idx = int(parts[3])
            rest = '.'.join(parts[4:])
            new_k = f"encoder.down_blocks.9.res_blocks.{layer_idx}.{rest}"
            
    # 3. Decoder mapping
    elif k.startswith("decoder.mid_block."):
        parts = k.split('.')
        if parts[2] == "resnets":
            layer_idx = int(parts[3])
            rest = '.'.join(parts[4:])
            new_k = f"decoder.up_blocks.0.res_blocks.{layer_idx}.{rest}"
            
    elif k.startswith("decoder.up_blocks."):
        parts = k.split('.')
        block_idx = int(parts[2])
        last_part = parts[-1]
        
        if block_idx == 0:
            if parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"decoder.up_blocks.1.res_blocks.{layer_idx}.{rest}"
                
        elif block_idx == 1:
            if parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"decoder.up_blocks.3.res_blocks.{layer_idx}.{rest}"
            elif parts[3] == "upsamplers":
                new_k = f"decoder.up_blocks.2.conv.conv.{last_part}"
                
        elif block_idx == 2:
            if parts[3] == "conv_in":
                if "conv_shortcut" in parts:
                    new_k = f"decoder.up_blocks.4.conv_shortcut.{last_part}"
                elif "norm3" in parts:
                    new_k = f"decoder.up_blocks.4.norm3.norm.{last_part}"
                else:
                    rest = '.'.join(parts[4:])
                    new_k = f"decoder.up_blocks.4.{rest}"
            elif parts[3] == "upsamplers":
                new_k = f"decoder.up_blocks.5.conv.conv.{last_part}"
            elif parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"decoder.up_blocks.6.res_blocks.{layer_idx}.{rest}"
                
        elif block_idx == 3:
            if parts[3] == "conv_in":
                if "conv_shortcut" in parts:
                    new_k = f"decoder.up_blocks.7.conv_shortcut.{last_part}"
                elif "norm3" in parts:
                    new_k = f"decoder.up_blocks.7.norm3.norm.{last_part}"
                else:
                    rest = '.'.join(parts[4:])
                    new_k = f"decoder.up_blocks.7.{rest}"
            elif parts[3] == "upsamplers":
                new_k = f"decoder.up_blocks.8.conv.conv.{last_part}"
            elif parts[3] == "resnets":
                layer_idx = int(parts[4])
                rest = '.'.join(parts[5:])
                new_k = f"decoder.up_blocks.9.res_blocks.{layer_idx}.{rest}"
                
    if new_k != k:
        mapped_count += 1
        
    new_sd[new_k] = v

print(f"Mapped {mapped_count} keys out of {len(sd)} keys.")
save_file(new_sd, dst_path)
print("Saved converted state dict.")
