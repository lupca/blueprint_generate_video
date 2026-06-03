import sys
import torch

sys.path.append('/root/ComfyUI')
from comfy.ldm.lightricks.vae.causal_video_autoencoder import VideoVAE

model = VideoVAE(version=0)
print("Model keys (first 100):")
for k in sorted(list(model.state_dict().keys()))[:100]:
    print(k)
