import aiohttp
import asyncio
from typing import Dict, Any, Optional
import json
from starlette.datastructures import UploadFile
import src.config as config

class OptimizedHTTPClient:
    """優化的 HTTP 客戶端，使用連接池和會話重用"""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """取得或建立 HTTP 會話"""
        if self._session is None or self._session.closed:
            async with self._lock:
                if self._session is None or self._session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=100,  # 總連接數限制
                        limit_per_host=30,  # 每個主機的連接數限制
                        ttl_dns_cache=300,  # DNS 快取時間
                        use_dns_cache=True,
                        keepalive_timeout=30,  # Keep-alive 超時
                        enable_cleanup_closed=True
                    )
                    timeout = aiohttp.ClientTimeout(
                        total=config.DEFAULT_GQL_EXEC_TIMEOUT,
                        connect=10,
                        sock_read=30
                    )
                    self._session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout,
                        headers={
                            'User-Agent': 'Mesh-Proxy-Server/1.0'
                        }
                    )
        return self._session
    
    async def post_json(self, url: str, data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """發送 JSON POST 請求"""
        session = await self.get_session()
        async with session.post(url, json=data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def post_form(self, url: str, data: Dict[str, Any], files: Dict[str, bytes], headers: Dict[str, str]) -> Dict[str, Any]:
        """發送表單 POST 請求"""
        session = await self.get_session()
        
        # 準備表單數據
        form_data = aiohttp.FormData()
        for key, value in data.items():
            form_data.add_field(key, str(value))
        
        for key, file_content in files.items():
            form_data.add_field(key, file_content, filename=f'{key}.bin')
        
        async with session.post(url, data=form_data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def close(self):
        """關閉會話"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

# 全域 HTTP 客戶端實例
_http_client = OptimizedHTTPClient()

async def get_http_client() -> OptimizedHTTPClient:
    """取得全域 HTTP 客戶端實例"""
    return _http_client

async def close_http_client():
    """關閉全域 HTTP 客戶端"""
    await _http_client.close() 