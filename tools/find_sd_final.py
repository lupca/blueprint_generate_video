import sys
sys.path.append('/root/ComfyUI')
try:
    import comfy.sd
    print(f"ACTIVE_SD_PATH: {comfy.sd.__file__}")
except Exception as e:
    print(f"Error importing comfy.sd: {e}")
    print(f"Current sys.path: {sys.path}")
