import pymongo
from pymongo import MongoClient
from typing import Optional
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

class MongoManager:
    """MongoDB 連接管理器，使用連接池"""
    
    def __init__(self):
        self._sync_client: Optional[MongoClient] = None
        self._async_client: Optional[AsyncIOMotorClient] = None
        self._lock = asyncio.Lock()
    
    def get_sync_client(self, mongo_url: str) -> MongoClient:
        """取得同步 MongoDB 客戶端"""
        if self._sync_client is None:
            self._sync_client = MongoClient(
                mongo_url,
                maxPoolSize=50,  # 連接池大小
                minPoolSize=10,  # 最小連接數
                maxIdleTimeMS=30000,  # 最大閒置時間
                serverSelectionTimeoutMS=5000,  # 伺服器選擇超時
                connectTimeoutMS=10000,  # 連接超時
                socketTimeoutMS=30000,  # Socket 超時
            )
        return self._sync_client
    
    async def get_async_client(self, mongo_url: str) -> AsyncIOMotorClient:
        """取得非同步 MongoDB 客戶端"""
        if self._async_client is None:
            async with self._lock:
                if self._async_client is None:
                    self._async_client = AsyncIOMotorClient(
                        mongo_url,
                        maxPoolSize=50,
                        minPoolSize=10,
                        maxIdleTimeMS=30000,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=10000,
                        socketTimeoutMS=30000,
                    )
        return self._async_client
    
    def get_sync_db(self, mongo_url: str, env: str = 'dev'):
        """取得同步資料庫實例"""
        client = self.get_sync_client(mongo_url)
        if env == 'staging':
            return client.staging
        elif env == 'prod':
            return client.prod
        else:
            return client.dev
    
    async def get_async_db(self, mongo_url: str, env: str = 'dev'):
        """取得非同步資料庫實例"""
        client = await self.get_async_client(mongo_url)
        if env == 'staging':
            return client.staging
        elif env == 'prod':
            return client.prod
        else:
            return client.dev
    
    async def close(self):
        """關閉所有連接"""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        
        if self._async_client:
            self._async_client.close()
            self._async_client = None

# 全域 MongoDB 管理器實例
_mongo_manager = MongoManager()

def get_mongo_manager() -> MongoManager:
    """取得全域 MongoDB 管理器"""
    return _mongo_manager

async def close_mongo_manager():
    """關閉全域 MongoDB 管理器"""
    await _mongo_manager.close() 