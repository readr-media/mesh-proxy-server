import json
import os
import hashlib
import re
from datetime import datetime, timezone
from google.cloud import storage
import jwt
import base64
import hmac

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

def decode_bearer_token(self, token):
    data = None
    try:
        data = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
    except Exception as e:
        print("decode bearer token failed, reason: ",str(e))
    return data

def get_isoformat_time(timestamp: int):
    dt = datetime.fromtimestamp(timestamp)
    iso_format = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return iso_format

def get_current_timestamp():
    return int(datetime.now().timestamp())

def sign_cookie(
    url_prefix: str,
    key_name: str,
    base64_key: str,
    expiration_time: datetime,
) -> str:
    """Gets the Signed cookie value for the specified URL prefix and configuration.

    Args:
        url_prefix: URL prefix to sign.
        key_name: name of the signing key.
        base64_key: signing key as a base64 encoded string.
        expiration_time: expiration time as time-zone aware datetime.

    Returns:
        Returns the Cloud-CDN-Cookie value based on the specified configuration.
    """
    encoded_url_prefix = base64.urlsafe_b64encode(
        url_prefix.strip().encode("utf-8")
    ).decode("utf-8")
    epoch = datetime.fromtimestamp(0, timezone.utc)
    expiration_timestamp = int((expiration_time - epoch).total_seconds())
    decoded_key = base64.urlsafe_b64decode(base64_key)

    policy = f"URLPrefix={encoded_url_prefix}:Expires={expiration_timestamp}:KeyName={key_name}"

    digest = hmac.new(decoded_key, policy.encode("utf-8"), hashlib.sha1).digest()
    signature = base64.urlsafe_b64encode(digest).decode("utf-8")

    signed_policy = f"Cloud-CDN-Cookie={policy}:Signature={signature}"

    return signed_policy