import json

path = '/root/blueprint_generate_video/workflows/workflow_ltxv_api.json'
with open(path, 'r') as f:
    wf = json.load(f)

# Change RIFE VFI input to take from LTXV Decode directly (node 12)
wf['16']['inputs']['frames'] = ['12', 0]

# Change ImageUpscaleWithModel input to take from RIFE VFI (node 16)
wf['15']['inputs']['image'] = ['16', 0]

# VideoCombine remains taking from node 15 (which is now after RIFE)
# Wait, let's verify node 13 input.
# In previous script: wf['13']['inputs']['images'] = ['16', 0]
# We want it to be ['15', 0] now.
wf['13']['inputs']['images'] = ['15', 0]

with open(path, 'w') as f:
    json.dump(wf, f, indent=2)

print('Workflow order updated successfully!')
