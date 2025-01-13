import json
import os
import hashlib
import re
from datetime import datetime
from google.cloud import storage

def read_blob(bucket_name, blob_name):
    data = None
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    with blob.open("r") as f:
        data = f.read()
    return data  

def save_file(dest_filename, data):
    if data:
        dirname = os.path.dirname(dest_filename)
        if len(dirname)>0 and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(dest_filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False))

def download_keyfile(bucket_name, blob_name: str, destination_filename: str):
    data = read_blob(bucket_name, blob_name)
    save_file(destination_filename, data=json.loads(data))

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

def get_current_timestamp():
    return int(datetime.now().timestamp())