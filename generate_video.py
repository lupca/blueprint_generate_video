import websocket
import uuid
import json
import urllib.request
import urllib.parse
import os
import subprocess
import time

server_address = '127.0.0.1:8188'
client_id = str(uuid.uuid4())
base_dir = '/root'

def queue_prompt(prompt):
    p = {'prompt': prompt, 'client_id': client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request('http://{}/prompt'.format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {'filename': filename, 'subfolder': subfolder, 'type': folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen('http://{}/view?{}'.format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen('http://{}/history/{}'.format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def generate_segment(workflow, flux_prompt, ltx_prompt, output_name):
    workflow['6']['inputs']['text'] = flux_prompt
    workflow['22']['inputs']['text'] = ltx_prompt
    
    ws = websocket.WebSocket()
    ws.connect('ws://{}/ws?clientId={}'.format(server_address, client_id))
    
    prompt_id = queue_prompt(workflow)['prompt_id']
    print(f'Queued task {output_name}: {prompt_id}')
    
    try:
        ws.settimeout(300.0) # 5-minute timeout per segment
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
    print(f"Polling history for prompt {prompt_id}...")
    for attempt in range(60): # up to 5 minutes
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
        return None
        
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'gifs' in node_output:
            video_data = node_output['gifs'][0]
            filename = video_data['filename']
            with open(os.path.join(base_dir, output_name), 'wb') as f:
                f.write(get_image(filename, video_data['subfolder'], video_data['type']))
            print(f'Segment {output_name} saved.')
            return output_name
    return None

def free_memory():
    req = urllib.request.Request('http://{}/free'.format(server_address), data=b'')
    try:
        with urllib.request.urlopen(req) as response:
            response.read()
        print("VRAM and model cache cleared from GPU successfully.")
    except Exception as e:
        print(f"Warning: Failed to free VRAM: {e}")

def main():
    workflow_path = os.path.join(base_dir, 'workflow_api.json')
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    segments = [
        ('A futuristic city at sunset', 'Cinematic drone shot flying through skyscrapers', 'part1.mp4'),
        ('Close up of a robotic eye', 'Mechanical iris opening and glowing neon blue', 'part2.mp4'),
        ('High-tech data center with glowing servers', 'Camera panning down a row of server racks', 'part3.mp4')
    ]
    
    results = []
    for flux_p, ltx_p, out_n in segments:
        res = generate_segment(workflow, flux_p, ltx_p, out_n)
        if res:
            results.append(res)
    
    # Force unload models to free GPU memory
    free_memory()
    
    if len(results) == 3:
        input_path = os.path.join(base_dir, 'inputs.txt')
        with open(input_path, 'w') as f:
            for r in results:
                f.write(f"file '{os.path.join(base_dir, r)}'\n")
        
        output_file = os.path.join(base_dir, 'final_commercial_15s.mp4')
        subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', input_path, '-c', 'copy', output_file], check=True)
        print(f'SUCCESS: {output_file} generated!')

if __name__ == '__main__':
    main()
