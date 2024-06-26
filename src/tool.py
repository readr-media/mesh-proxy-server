import json
import os
import requests
import hashlib

def save_file(dest_filename, data):
    if data:
        dirname = os.path.dirname(dest_filename)
        if len(dirname)>0 and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(dest_filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False))
        
def save_keyfile_from_url(url: str, path: str):
    res = requests.get(url)
    save_file(path, res.json())
    
def key_builder(
    prefix: str = "",
    request: str = "",
) -> str:
    cache_key = hashlib.md5(  # noqa: S324
        f"{request}".encode()
    ).hexdigest()
    return f"{prefix}:{cache_key}"