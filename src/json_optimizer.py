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

def fast_json_dumps(obj: Any, **kwargs) -> str:
    """使用 orjson 進行快速 JSON 序列化，支援標準 json.dumps 參數"""
    # 處理 orjson 不支援的參數
    options = orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC | orjson.OPT_OMIT_MICROSECONDS
    
    # 處理 ensure_ascii 參數
    if kwargs.get('ensure_ascii', True) is False:
        options |= orjson.OPT_UNICODE_ESCAPE
    
    # 處理 indent 參數（orjson 不支援，但我們可以忽略）
    if 'indent' in kwargs:
        # orjson 不支援 indent，但我們可以忽略這個參數
        pass
    
    # 處理 separators 參數（orjson 不支援，但我們可以忽略）
    if 'separators' in kwargs:
        # orjson 不支援自定義分隔符，但我們可以忽略這個參數
        pass
    
    # 處理 sort_keys 參數
    if kwargs.get('sort_keys', False):
        options |= orjson.OPT_SORT_KEYS
    
    return orjson.dumps(obj, option=options).decode('utf-8')

def fast_json_loads(s: str, **kwargs) -> Any:
    """使用 orjson 進行快速 JSON 反序列化，支援標準 json.loads 參數"""
    # orjson.loads 不支援額外參數，但我們可以忽略它們以保持相容性
    return orjson.loads(s)

# 替換標準的 json 模組
json.dumps = fast_json_dumps
json.loads = fast_json_loads 