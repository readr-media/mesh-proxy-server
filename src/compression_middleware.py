import gzip
import json
from typing import Any, Dict
# 確保 JSON 優化生效
import src.json_optimizer
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from src.json_optimizer import fast_json_dumps

class CompressionMiddleware:
    """回應壓縮中間件，減少網路傳輸量"""
    
    @staticmethod
    def should_compress(content: Any, min_size: int = 1000) -> bool:
        """判斷是否需要壓縮"""
        if isinstance(content, (dict, list)):
            content_str = fast_json_dumps(content)
        else:
            content_str = str(content)
        
        return len(content_str.encode('utf-8')) >= min_size
    
    @staticmethod
    def compress_content(content: Any) -> bytes:
        """壓縮內容"""
        if isinstance(content, (dict, list)):
            content_str = fast_json_dumps(content)
        else:
            content_str = str(content)
        
        return gzip.compress(content_str.encode('utf-8'))
    
    @staticmethod
    async def compress_response(request: Request, content: Any, min_size: int = 1000) -> Response:
        """壓縮回應"""
        # 檢查客戶端是否支援 gzip
        accept_encoding = request.headers.get('accept-encoding', '')
        supports_gzip = 'gzip' in accept_encoding.lower()
        
        if not supports_gzip or not CompressionMiddleware.should_compress(content, min_size):
            # 不壓縮，使用標準 JSONResponse
            return JSONResponse(content=content)
        
        # 壓縮內容
        compressed_data = CompressionMiddleware.compress_content(content)
        
        # 建立壓縮回應
        response = Response(
            content=compressed_data,
            media_type='application/json',
            headers={
                'Content-Encoding': 'gzip',
                'Content-Length': str(len(compressed_data)),
                'Vary': 'Accept-Encoding'
            }
        )
        
        return response

def get_compressed_response(request: Request, content: Any, min_size: int = 1000) -> Response:
    """取得壓縮回應的便捷函數"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已經在事件迴圈中，使用同步版本
            return CompressionMiddleware.compress_response_sync(request, content, min_size)
        else:
            # 如果不在事件迴圈中，直接執行
            return loop.run_until_complete(
                CompressionMiddleware.compress_response(request, content, min_size)
            )
    except RuntimeError:
        # 如果沒有事件迴圈，使用同步版本
        return CompressionMiddleware.compress_response_sync(request, content, min_size)
    
    @staticmethod
    def compress_response_sync(request: Request, content: Any, min_size: int = 1000) -> Response:
        """同步版本的壓縮回應"""
        # 檢查客戶端是否支援 gzip
        accept_encoding = request.headers.get('accept-encoding', '')
        supports_gzip = 'gzip' in accept_encoding.lower()
        
        if not supports_gzip or not CompressionMiddleware.should_compress(content, min_size):
            # 不壓縮，使用標準 JSONResponse
            return JSONResponse(content=content)
        
        # 壓縮內容
        compressed_data = CompressionMiddleware.compress_content(content)
        
        # 建立壓縮回應
        response = Response(
            content=compressed_data,
            media_type='application/json',
            headers={
                'Content-Encoding': 'gzip',
                'Content-Length': str(len(compressed_data)),
                'Vary': 'Accept-Encoding'
            }
        )
        
        return response 