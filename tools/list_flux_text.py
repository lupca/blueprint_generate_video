from huggingface_hub import list_repo_files
try:
    files = list_repo_files(repo_id='comfyanonymous/flux_text_encoders')
    for f in files:
        print(f)
except Exception as e:
    print(f'Error listing files: {e}')
