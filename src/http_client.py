import aiohttp
import asyncio
from typing import Optional, Dict, Any
import json
import os

class OptimizedHTTPClient:
    """
    優化的 HTTP 客戶端，使用 aiohttp 實現連接池和會話重用
    """
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
    async def _ensure_session(self):
        """確保會話已建立"""
        if self._session is None or self._session.closed:
            # 建立連接器，設定連接池大小
            self._connector = aiohttp.TCPConnector(
                limit=100,  # 總連接數限制
                limit_per_host=30,  # 每個主機的連接數限制
                keepalive_timeout=30,  # 保持連接時間
                enable_cleanup_closed=True,  # 清理關閉的連接
                ttl_dns_cache=300,  # DNS 快取時間
            )
            
            # 建立會話
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mesh-Proxy-Server/1.0',
                    'Content-Type': 'application/json',
                }
            )
    
    async def post_json(self, url: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        發送 JSON POST 請求
        """
        await self._ensure_session()
        
        try:
            async with self._session.post(
                url,
                json=data,
                headers=headers,
                ssl=False  # 在開發環境中可能需要
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"   ✅ HTTP 響應成功")
                return result
        except aiohttp.ClientError as e:
            print(f"❌ HTTP 請求錯誤: {e}")
            raise e
    
    async def post_form(self, url: str, data: Dict[str, Any], files: Dict[str, bytes], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        發送表單 POST 請求（支援檔案上傳）
        """
        await self._ensure_session()
        
        try:
            # 準備表單資料
            form_data = aiohttp.FormData()
            
            # 添加一般資料
            for key, value in data.items():
                form_data.add_field(key, str(value))
            
            # 添加檔案
            for key, file_content in files.items():
                form_data.add_field(key, file_content, filename=f'{key}.file')
            
            async with self._session.post(
                url,
                data=form_data,
                headers=headers,
                ssl=False
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"HTTP form request error: {e}")
            raise e
    
    async def close(self):
        """關閉會話和連接器"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector and not self._connector.closed:
            await self._connector.close()

# 全域 HTTP 客戶端實例
_http_client: Optional[OptimizedHTTPClient] = None

async def get_http_client() -> OptimizedHTTPClient:
    """取得全域 HTTP 客戶端實例"""
    global _http_client
    if _http_client is None:
        _http_client = OptimizedHTTPClient()
    return _http_client

async def close_http_client():
    """關閉全域 HTTP 客戶端"""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None 