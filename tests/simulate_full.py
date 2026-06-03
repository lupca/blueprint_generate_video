import torch
from safetensors.torch import load_file
import os

path = os.path.expanduser('~/ComfyUI/models/vae/ltx_video_vae.safetensors')
sd = load_file(path)

print(f"Total keys: {len(sd)}")

# Simulate the if/elif chain
if "decoder.mid.block_1.mix_factor" in sd:
    print("Matched: decoder.mid.block_1.mix_factor")
elif "taesd_decoder.1.weight" in sd:
    print("Matched: taesd_decoder.1.weight")
elif "vquantizer.codebook.weight" in sd:
    print("Matched: vquantizer.codebook.weight")
elif "backbone.1.0.block.0.1.num_batches_tracked" in sd:
    print("Matched: backbone.1.0.block.0.1.num_batches_tracked")
elif "blocks.11.num_batches_tracked" in sd:
    print("Matched: blocks.11.num_batches_tracked")
elif "encoder.backbone.1.0.block.0.1.num_batches_tracked" in sd:
    print("Matched: encoder.backbone.1.0.block.0.1.num_batches_tracked")
elif "decoder.conv_in.weight" in sd:
    print("Matched: decoder.conv_in.weight")
elif "decoder.layers.1.layers.0.beta" in sd:
    print("Matched: decoder.layers.1.layers.0.beta")
elif "blocks.2.blocks.3.stack.5.weight" in sd or "decoder.blocks.2.blocks.3.stack.5.weight" in sd or "layers.4.layers.1.attn_block.attn.qkv.weight" in sd or "encoder.layers.4.layers.1.attn_block.attn.qkv.weight" in sd:
    print("Matched: genmo mochi vae")
elif "decoder.up_blocks.0.res_blocks.0.conv1.conv.weight" in sd or "decoder.up_blocks.0.resnets.0.conv1.conv.weight" in sd:
    print("Matched: lightricks ltxv (Our patch)")
elif "decoder.conv_in.conv.weight" in sd and sd['decoder.conv_in.conv.weight'].shape[1] == 32:
    print("Matched: hunyuan refiner")
elif "decoder.conv_in.conv.weight" in sd and "decoder.mid_block.resnets.0.norm1.norm_layer.weight" in sd:
    print("Matched: cogvideox")
elif "decoder.conv_in.conv.weight" in sd:
    print("Matched: decoder.conv_in.conv.weight (Line 697 fallback)")
elif "decoder.unpatcher3d.wavelets" in sd:
    print("Matched: cosmos")
elif "decoder.middle.0.residual.0.gamma" in sd:
    print("Matched: wan")
else:
    print("Matched: default SD1.x/SD2.x/Flux")

