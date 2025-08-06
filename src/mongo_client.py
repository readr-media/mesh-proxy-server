import motor.motor_asyncio
import pymongo
from typing import Optional, Dict, Any
import os
import asyncio

class MongoManager:
    """
    MongoDB 連接管理器，使用 motor 實現連接池和非同步操作
    """
    
    def __init__(self):
        self._async_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._sync_client: Optional[pymongo.MongoClient] = None
        self._mongo_url: Optional[str] = None
        self._env: str = 'dev'
        
    async def initialize(self, mongo_url: str, env: str = 'dev'):
        """初始化 MongoDB 連接"""
        if self._async_client is None or self._mongo_url != mongo_url or self._env != env:
            # 關閉現有連接
            await self.close()
            
            self._mongo_url = mongo_url
            self._env = env
            
            # 建立非同步客戶端（使用 motor）
            self._async_client = motor.motor_asyncio.AsyncIOMotorClient(
                mongo_url,
                maxPoolSize=50,  # 連接池大小
                minPoolSize=10,  # 最小連接數
                maxIdleTimeMS=30000,  # 最大空閒時間
                waitQueueTimeoutMS=5000,  # 等待隊列超時
                serverSelectionTimeoutMS=5000,  # 服務器選擇超時
                connectTimeoutMS=10000,  # 連接超時
                socketTimeoutMS=30000,  # Socket 超時
            )
            
            # 建立同步客戶端（用於向後相容）
            self._sync_client = pymongo.MongoClient(
                mongo_url,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                waitQueueTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=30000,
            )
            
            print(f"MongoDB 連接池已初始化 - 環境: {env}")
    
    def get_async_client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        """取得非同步 MongoDB 客戶端"""
        if self._async_client is None:
            raise RuntimeError("MongoDB 客戶端尚未初始化")
        return self._async_client
    
    def get_sync_client(self) -> pymongo.MongoClient:
        """取得同步 MongoDB 客戶端（向後相容）"""
        if self._sync_client is None:
            raise RuntimeError("MongoDB 客戶端尚未初始化")
        return self._sync_client
    
    def get_async_db(self):
        """取得非同步資料庫實例"""
        client = self.get_async_client()
        db_name = None
        if self._env == 'staging':
            db = client.staging
            db_name = 'staging'
        elif self._env == 'prod':
            db = client.prod
            db_name = 'prod'
        else:
            db = client.dev
            db_name = 'dev'
        
        print(f"   📊 使用資料庫: {db_name}")
        return db
    
    def get_sync_db(self):
        """取得同步資料庫實例（向後相容）"""
        client = self.get_sync_client()
        if self._env == 'staging':
            return client.staging
        elif self._env == 'prod':
            return client.prod
        else:
            return client.dev
    
    async def close(self):
        """關閉所有連接"""
        if self._async_client:
            self._async_client.close()
            self._async_client = None
        
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        
        self._mongo_url = None
        print("MongoDB 連接已關閉")

# 全域 MongoDB 管理器實例
_mongo_manager: Optional[MongoManager] = None

async def get_mongo_manager() -> MongoManager:
    """取得全域 MongoDB 管理器實例"""
    global _mongo_manager
    if _mongo_manager is None:
        print(f"🔧 創建新的 MongoDB 管理器實例")
        _mongo_manager = MongoManager()
    else:
        print(f"🔧 使用現有的 MongoDB 管理器實例")
    return _mongo_manager

async def initialize_mongo(mongo_url: str, env: str = 'dev'):
    """初始化 MongoDB 連接"""
    manager = await get_mongo_manager()
    await manager.initialize(mongo_url, env)

async def close_mongo():
    """關閉 MongoDB 連接"""
    global _mongo_manager
    if _mongo_manager:
        await _mongo_manager.close()
        _mongo_manager = None

# 向後相容的函數
def connect_db(mongo_url: str, env: str = 'dev'):
    """向後相容的同步連接函數"""
    client = pymongo.MongoClient(
        mongo_url,
        maxPoolSize=50,
        minPoolSize=10,
        maxIdleTimeMS=30000,
        waitQueueTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=30000,
    )
    
    if env == 'staging':
        return client.staging
    elif env == 'prod':
        return client.prod
    else:
        return client.dev 