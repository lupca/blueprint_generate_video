import json

path = '/root/blueprint_generate_video/workflows/workflow_ltxv_api.json'
with open(path, 'r') as f:
    wf = json.load(f)

# Replace Node 15 (Model Upscale) with simple ImageScale to 1080p
wf['15'] = {
    'inputs': {
        'upscale_method': 'bicubic',
        'width': 1620, # Let's stay a bit below 1080p for safety or use 1080p
        'height': 1080,
        'crop': 'disabled',
        'image': ['12', 0]
    },
    'class_type': 'ImageScale'
}
# Recalculate width for 1080p height (768/512 = 1.5. 1080 * 1.5 = 1620)
wf['15']['inputs']['width'] = 1620

# Node 16 (RIFE) takes from node 15
wf['16']['inputs']['frames'] = ['15', 0]

# Node 13 (Combine) takes from node 16
wf['13']['inputs']['images'] = ['16', 0]

# Delete node 14 (Model Loader)
if '14' in wf: del wf['14']

with open(path, 'w') as f:
    json.dump(wf, f, indent=2)

print('Workflow optimized for 4060 Ti memory limits!')
