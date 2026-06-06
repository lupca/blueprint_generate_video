import websocket
import uuid
import json
import urllib.request
import urllib.parse
import os
import argparse
import time

server_address = os.environ.get('COMFYUI_SERVER_ADDRESS', 'localhost:8188')
if server_address.startswith('http://'):
    server_address = server_address[7:]
elif server_address.startswith('https://'):
    server_address = server_address[8:]

client_id = str(uuid.uuid4())
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def queue_prompt(prompt):
    p = {'prompt': prompt, 'client_id': client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request('http://{}/prompt'.format(server_address), data=data, headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {'filename': filename, 'subfolder': subfolder, 'type': folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen('http://{}/view?{}'.format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen('http://{}/history/{}'.format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def free_memory():
    req = urllib.request.Request('http://{}/free'.format(server_address), data=b'{}', headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            response.read()
        print("VRAM and model cache cleared from GPU successfully.")
    except Exception as e:
        print(f"Warning: Failed to free VRAM: {e}")

def main():
    parser = argparse.ArgumentParser(description="Flux.1 Schnell Image Generation API")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt for image generation")
    parser.add_argument("--output", type=str, default="flux_output.png", help="Filename/path to save the generated image")
    args = parser.parse_args()

    workflow_path = os.path.join(base_dir, 'workflows/workflow_flux_api.json')
    if not os.path.exists(workflow_path):
        print(f"Error: {workflow_path} not found.")
        return

    with open(workflow_path, 'r') as f:
        workflow = json.load(f)

    # Inject prompt into workflow (node 6)
    workflow['6']['inputs']['text'] = args.prompt

    print("Connecting to ComfyUI server...")
    ws = websocket.WebSocket()
    ws.connect('ws://{}/ws?clientId={}'.format(server_address, client_id))

    prompt_id = queue_prompt(workflow)['prompt_id']
    print(f"Queued image generation task. Prompt ID: {prompt_id}")

    # Listen for completion
    try:
        ws.settimeout(120.0)  # 2 minute timeout for image gen
        while True:
            try:
                out = ws.recv()
                if not out:
                    break
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break
            except Exception as e:
                print(f"WebSocket read error/timeout: {e}. Falling back to history polling...")
                break
    finally:
        try:
            ws.close()
        except Exception:
            pass

    # Poll history until prompt completion is verified and available
    history = None
    print("Polling history...")
    for attempt in range(24):  # up to 2 minutes
        try:
            history_data = get_history(prompt_id)
            if prompt_id in history_data:
                history = history_data[prompt_id]
                break
        except Exception:
            pass
        time.sleep(5)

    if not history:
        print(f"Error: Prompt {prompt_id} did not appear in history.")
        free_memory()
        return

    # Free GPU VRAM
    free_memory()

    # Find saved image in output
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            img_data = node_output['images'][0]
            filename = img_data['filename']
            output_filepath = os.path.join(base_dir, args.output) if not os.path.isabs(args.output) else args.output
            with open(output_filepath, 'wb') as f:
                f.write(get_image(filename, img_data.get('subfolder', ''), img_data.get('type', 'output')))
            print(f"SUCCESS: Image saved to {output_filepath}")
            return

    print("Error: Saved image output not found in history outputs.")

if __name__ == '__main__':
    main()
