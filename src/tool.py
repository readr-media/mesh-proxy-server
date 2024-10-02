import json
import os
import requests
import hashlib
import re
from datetime import datetime

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

# Extreact jwt token from "Bearer <jwt_token>"
def extract_bearer_token(bearer_token):
    if bearer_token==None:
        return None
    pattern = r'Bearer\s+(\S+)' 
    match = re.search(pattern, bearer_token)
    if match:
        return match.group(1)
    return None

def get_isoformat_time(timestamp: int):
    dt = datetime.fromtimestamp(timestamp)
    iso_format = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return iso_format