import json

path = '/root/blueprint_generate_video/workflows/workflow_ltxv_api.json'
with open(path, 'r') as f:
    wf = json.load(f)

# Update RIFE VFI node
wf['16']['inputs']['torch_compile'] = False
wf['16']['inputs']['batch_size'] = 1
wf['16']['inputs']['dtype'] = 'fp16'

with open(path, 'w') as f:
    json.dump(wf, f, indent=2)

print('Workflow updated successfully!')
