import hashlib

def gql_key_builder(
    prefix: str = "",
    request: str = "",
) -> str:
    cache_key = hashlib.md5(  # noqa: S324
        f"{request}".encode()
    ).hexdigest()
    return f"{prefix}:{cache_key}"