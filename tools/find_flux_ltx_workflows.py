import os

found_files = []
for root, dirs, files in os.walk('/root'):
    # Skip cache and node_modules
    if '.cache' in root or '.npm' in root or 'node_modules' in root or '.git' in root:
        continue
    for f in files:
        if f.endswith('.json'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', errors='ignore') as file_obj:
                    content = file_obj.read().lower()
                    if 'flux' in content and 'ltx' in content:
                        found_files.append((path, len(content)))
            except Exception:
                pass

print("Matching files found:")
for p, s in found_files:
    print(f"  {p} ({s} bytes)")
