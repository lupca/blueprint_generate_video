from huggingface_hub import list_repo_files
try:
    files = list_repo_files(repo_id='Kijai/flux-fp8')
    for f in files:
        print(f)
except Exception as e:
    print(f'Error: {e}')
