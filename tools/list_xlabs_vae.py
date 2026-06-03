from huggingface_hub import list_repo_files
try:
    files = list_repo_files(repo_id='XLabs-AI/flux-vae')
    for f in files:
        print(f)
except Exception as e:
    print(f'Error: {e}')
