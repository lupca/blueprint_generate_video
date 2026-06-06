import json

path = '/root/blueprint_generate_video/workflows/workflow_ltxv_api.json'
with open(path, 'r') as f:
    wf = json.load(f)

# Add UpscaleModelLoader
wf['14'] = {
    'inputs': {'model_name': '4x-UltraSharp.pth'},
    'class_type': 'UpscaleModelLoader'
}

# Add ImageUpscaleWithModel
wf['15'] = {
    'inputs': {
        'upscale_model': ['14', 0],
        'image': ['12', 0]
    },
    'class_type': 'ImageUpscaleWithModel'
}

# Add RIFE VFI
wf['16'] = {
    'inputs': {
        'ckpt_name': 'rife47.pth',
        'clear_cache_after_n_frames': 10,
        'multiplier': 2,
        'fast_mode': True,
        'ensemble': True,
        'scale_factor': 1.0,
        'frames': ['15', 0]
    },
    'class_type': 'RIFE VFI'
}

# Update VideoCombine input to take frames from RIFE VFI
wf['13']['inputs']['images'] = ['16', 0]

with open(path, 'w') as f:
    json.dump(wf, f, indent=2)

print('Workflow updated successfully!')
