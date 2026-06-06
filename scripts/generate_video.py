import websocket
import uuid
import json
import urllib.request
import urllib.parse
import os
import argparse
import subprocess
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

def upload_image(filepath):
    import mimetypes
    filename = os.path.basename(filepath)
    if not os.path.exists(filepath):
        print(f"Error: image file to upload does not exist: {filepath}")
        return None
        
    with open(filepath, 'rb') as f:
        file_content = f.read()
        
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
    
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f'Content-Type: {mimetypes.guess_type(filepath)[0] or "image/png"}\r\n\r\n'
    ).encode('utf-8') + file_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(f'http://{server_address}/upload/image', data=body, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read())
            print(f"Uploaded {filepath} successfully as {res['name']}")
            return res['name']
    except Exception as e:
        print(f"Error uploading image {filepath}: {e}")
        return None

def extract_last_frame(video_path, output_image_path):
    print(f"Extracting last frame from {video_path}...")
    # LTXV generates 121 frames. Frame index 120 is the exact last frame.
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', 'select=eq(n\\,120)',
        '-vframes', '1',
        output_image_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(output_image_path):
        print(f"Last frame extracted to {output_image_path}")
        return True
    else:
        print(f"Precise frame selection failed, attempting fallback seek...")
        # Fallback: Seek to end
        cmd_fallback = [
            'ffmpeg', '-y',
            '-sseof', '-0.1',
            '-i', video_path,
            '-update', '1',
            '-q:v', '1',
            '-frames:v', '1',
            output_image_path
        ]
        res_fb = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if res_fb.returncode == 0 and os.path.exists(output_image_path):
            print(f"Last frame extracted via fallback to {output_image_path}")
            return True
        else:
            print("Error: Failed to extract last frame.")
            return False

def free_memory():
    req = urllib.request.Request('http://{}/free'.format(server_address), data=b'{}', headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            response.read()
        print("VRAM and model cache cleared from GPU successfully.")
    except Exception as e:
        print(f"Warning: Failed to free VRAM: {e}")

def generate_segment(workflow, prompt, image_filename, output_name):
    # Set text prompt (node 22)
    workflow['22']['inputs']['text'] = prompt
    
    # Configure image-to-video vs text-to-video
    if image_filename:
        workflow['4']['inputs']['image'] = image_filename
        workflow['7']['inputs']['bypass_i2v'] = False
    else:
        workflow['7']['inputs']['bypass_i2v'] = True
        
    print(f"Connecting to ComfyUI websocket for segment {output_name}...")
    ws = websocket.WebSocket()
    ws.connect('ws://{}/ws?clientId={}'.format(server_address, client_id))
    
    prompt_id = queue_prompt(workflow)['prompt_id']
    print(f"Queued segment task. Prompt ID: {prompt_id}")
    
    try:
        ws.settimeout(300.0)  # 5 minute timeout per segment
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
    for attempt in range(60):  # up to 5 minutes
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
            filepath = os.path.join(base_dir, output_name)
            with open(filepath, 'wb') as f:
                f.write(get_image(filename, video_data.get('subfolder', ''), video_data.get('type', 'output')))
            print(f"Segment {output_name} saved.")
            return filepath
    return None

def main():
    parser = argparse.ArgumentParser(description="LTX-Video Pure Video Generation API")
    parser.add_argument("--prompt", type=str, required=True, help="Text motion prompt describing the action")
    parser.add_argument("--image", type=str, default="", help="Optional local path to starting reference image (Image-to-Video)")
    parser.add_argument("--duration", type=int, default=5, help="Desired length of the video in seconds (multiple of 5, e.g. 5, 10, 15)")
    parser.add_argument("--output", type=str, default="final_output.mp4", help="Filename/path to save the final stitched video")
    args = parser.parse_args()

    workflow_path = os.path.join(base_dir, 'workflows/workflow_ltxv_api.json')
    if not os.path.exists(workflow_path):
        print(f"Error: {workflow_path} not found.")
        return

    with open(workflow_path, 'r') as f:
        workflow = json.load(f)

    # Determine number of 5s segments
    num_segments = max(1, args.duration // 5)
    print(f"Configured generation: {args.duration}s total duration, using {num_segments} segment(s).")

    segment_files = []
    current_image_filename = None

    # Step 1: Upload initial reference image if provided
    if args.image:
        image_abs_path = os.path.abspath(args.image)
        print(f"Uploading initial reference image: {image_abs_path}...")
        current_image_filename = upload_image(image_abs_path)
        if not current_image_filename:
            print("Error uploading reference image. Aborting.")
            free_memory()
            return
    else:
        print("No reference image provided. Segment 1 will generate in Text-to-Video mode.")

    # Step 2: Generate segments auto-regressively
    for idx in range(num_segments):
        seg_name = f"temp_seg_{idx+1}.mp4"
        print(f"\n--- Generating Segment {idx+1}/{num_segments} ({seg_name}) ---")
        
        # Run generation
        filepath = generate_segment(workflow, args.prompt, current_image_filename, seg_name)
        if not filepath:
            print(f"Error: Failed to generate segment {idx+1}. Aborting.")
            free_memory()
            return
            
        segment_files.append(filepath)
        
        # Prepare for next segment: Extract last frame of current segment
        if idx < num_segments - 1:
            frame_path = os.path.join(base_dir, "temp_last_frame.png")
            if not extract_last_frame(filepath, frame_path):
                print("Error: Could not extract last frame for sequential continuity. Aborting.")
                free_memory()
                return
            # Upload extracted frame as starting image for next segment
            current_image_filename = upload_image(frame_path)
            if not current_image_filename:
                print("Error: Failed to upload extracted last frame to ComfyUI. Aborting.")
                free_memory()
                return

    # Force VRAM release
    free_memory()

    # Step 3: Stitch/Compile final video
    print("\n--- Compiling Final Video ---")
    output_filepath = os.path.join(base_dir, args.output) if not os.path.isabs(args.output) else args.output
    
    if len(segment_files) == 1:
        # Single segment, just rename/copy
        print(f"Renaming {segment_files[0]} to {output_filepath}...")
        if os.path.exists(output_filepath):
            os.remove(output_filepath)
        os.rename(segment_files[0], output_filepath)
        print(f"SUCCESS: {output_filepath} generated successfully!")
    else:
        # Multi segment, stitch using FFmpeg Concat Demuxer
        inputs_path = os.path.join(base_dir, "inputs.txt")
        with open(inputs_path, 'w') as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")
        
        print(f"Stitching {len(segment_files)} segments into {output_filepath}...")
        res = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', inputs_path,
            '-c', 'copy',
            output_filepath
        ], capture_output=True, text=True)
        
        if res.returncode == 0:
            print(f"SUCCESS: {output_filepath} generated successfully!")
        else:
            print("Error: FFmpeg stitching failed.")
            print(res.stderr)
            
        # Clean up temporary stitch files
        if os.path.exists(inputs_path):
            os.remove(inputs_path)

    # Clean up segment files
    for seg in segment_files:
        if os.path.exists(seg):
            os.remove(seg)
            
    temp_frame = os.path.join(base_dir, "temp_last_frame.png")
    if os.path.exists(temp_frame):
        os.remove(temp_frame)

if __name__ == '__main__':
    main()
