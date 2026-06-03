import urllib.request
import json

url = "http://127.0.0.1:8188/object_info"
try:
    with urllib.request.urlopen(url) as response:
        info = json.loads(response.read())
    
    # Print custom nodes related to LTXV or loaders
    ltxv_nodes = [k for k in info.keys() if "ltxv" in k.lower() or "gguf" in k.lower()]
    print("Found custom LTXV/GGUF nodes:")
    for n in ltxv_nodes:
        print(f"  Node: {n}")
        print(f"    Inputs: {info[n]['input']}")
except Exception as e:
    print(f"Error querying API: {e}")
