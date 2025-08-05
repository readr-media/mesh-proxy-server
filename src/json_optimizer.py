import json
import orjson
from typing import Any, Dict, List
from fastapi.responses import JSONResponse

class OptimizedJSONResponse(JSONResponse):
    """優化的 JSON 回應，使用 orjson 進行更快的序列化"""
    
    def __init__(self, content: Any, **kwargs):
        super().__init__(content, **kwargs)
    
    def render(self, content: Any) -> bytes:
        return orjson.dumps(
            content,
            option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC | orjson.OPT_OMIT_MICROSECONDS
        )

def fast_json_dumps(obj: Any) -> str:
    """使用 orjson 進行快速 JSON 序列化"""
    return orjson.dumps(
        obj,
        option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC | orjson.OPT_OMIT_MICROSECONDS
    ).decode('utf-8')

def fast_json_loads(s: str) -> Any:
    """使用 orjson 進行快速 JSON 反序列化"""
    return orjson.loads(s)

# 替換標準的 json 模組
json.dumps = fast_json_dumps
json.loads = fast_json_loads 