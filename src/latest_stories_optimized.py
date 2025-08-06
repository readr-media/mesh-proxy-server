import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import src.config as config
from src.cache import get_cache, set_cache, mget_cache
from src.tool import key_builder
from fastapi_cache import FastAPICache
from src.performance_monitor import PerformanceMonitor, monitor_stage
from src.log import send_performance_logging

# 優化的快取配置
LATEST_STORIES_CACHE_TTL = int(os.environ.get('LATEST_STORIES_CACHE_TTL', 600))   # 10分鐘
LATEST_STORIES_EXPIRE_TIME = int(os.environ.get('LATEST_STORIES_EXPIRE_TIME', 300))  # 5分鐘
LATEST_STORIES_BACKGROUND_UPDATE = os.environ.get('LATEST_STORIES_BACKGROUND_UPDATE', 'true').lower() == 'true'

# 背景更新任務
_background_update_tasks: Dict[str, asyncio.Task] = {}

async def get_latest_stories_optimized(
    publishers: List[str],
    category: str,
    index: int = config.DEFAULT_LATEST_STORIES_INDEX,
    take: int = config.DEFAULT_LATEST_STORIES_TAKE,
    monitor: Optional[PerformanceMonitor] = None
) -> Dict[str, Any]:
    """
    優化的最新新聞獲取函數
    """
    start_time = datetime.now()
    prefix = FastAPICache.get_prefix()
    
    try:
        # 1. 從快取獲取數據
        if monitor:
            async with monitor_stage(monitor, "cache_retrieval"):
                cache_data = await _get_cached_stories(publishers, category, prefix)
        else:
            cache_data = await _get_cached_stories(publishers, category, prefix)
        
        # 2. 檢查是否需要更新
        needs_update = _check_update_needed(cache_data)
        
        # 3. 如果需要更新且啟用背景更新，觸發背景更新
        if needs_update and LATEST_STORIES_BACKGROUND_UPDATE:
            if monitor:
                async with monitor_stage(monitor, "background_update_trigger"):
                    await _trigger_background_update(publishers, category, prefix)
            else:
                await _trigger_background_update(publishers, category, prefix)
        
        # 4. 處理和組織數據
        if monitor:
            async with monitor_stage(monitor, "data_processing"):
                response = await _process_stories_data(cache_data, index, take, start_time)
        else:
            response = await _process_stories_data(cache_data, index, take, start_time)
        
        return response
        
    except Exception as e:
        print(f"Error in get_latest_stories_optimized: {e}")
        # 返回錯誤響應
        return {
            "error": str(e),
            "update_time": int(datetime.now().timestamp()),
            "expire_time": int((datetime.now() + timedelta(seconds=LATEST_STORIES_EXPIRE_TIME)).timestamp()),
            "num_stories": 0,
            "stories": []
        }

async def _get_cached_stories(publishers: List[str], category: str, prefix: str) -> Dict[str, Any]:
    """
    從快取獲取故事數據
    """
    all_keys = []
    for publisher_id in publishers:
        key = key_builder(f"{prefix}:category_latest", f"{category}:{publisher_id}")
        all_keys.append(key)
    
    values = await mget_cache(all_keys)
    print(f"Cache keys: {all_keys}")
    
    return {
        "keys": all_keys,
        "values": values,
        "publishers": publishers,
        "category": category
    }

def _check_update_needed(cache_data: Dict[str, Any]) -> bool:
    """
    檢查是否需要更新快取
    """
    values = cache_data.get("values", [])
    if not values:
        return True
    
    # 檢查是否有任何數據為空或過期
    current_time = datetime.now().timestamp()
    for value in values:
        if value is None:
            return True
        
        try:
            data = json.loads(value)
            update_time = data.get('update_time', 0)
            expire_time = update_time + LATEST_STORIES_EXPIRE_TIME
            
            if current_time > expire_time:
                return True
        except (json.JSONDecodeError, KeyError):
            return True
    
    return False

async def _trigger_background_update(publishers: List[str], category: str, prefix: str):
    """
    觸發背景更新任務
    """
    task_key = f"{category}:{','.join(sorted(publishers))}"
    
    # 檢查是否已經有正在執行的更新任務
    if task_key in _background_update_tasks:
        task = _background_update_tasks[task_key]
        if not task.done():
            print(f"Background update task already running for {task_key}")
            return
    
    # 創建新的背景更新任務
    task = asyncio.create_task(_background_update_stories(publishers, category, prefix))
    _background_update_tasks[task_key] = task
    
    # 清理完成的任務
    _cleanup_completed_tasks()

async def _background_update_stories(publishers: List[str], category: str, prefix: str):
    """
    背景更新故事數據
    """
    try:
        print(f"Starting background update for {category}:{publishers}")
        
        # 這裡應該調用實際的數據更新邏輯
        # 例如：從 GraphQL 獲取最新數據並更新快取
        # 為了演示，我們只是模擬更新過程
        
        await asyncio.sleep(2)  # 模擬更新時間
        
        # 更新快取
        current_time = int(datetime.now().timestamp())
        for publisher_id in publishers:
            key = key_builder(f"{prefix}:category_latest", f"{category}:{publisher_id}")
            
            # 這裡應該獲取實際的最新數據
            # 目前使用模擬數據
            mock_data = {
                "update_time": current_time,
                "data": [
                    {
                        "id": f"story_{publisher_id}_{current_time}",
                        "title": f"最新新聞 {publisher_id}",
                        "published_date": datetime.now().isoformat() + "Z",
                        "source": {"id": publisher_id, "title": f"來源 {publisher_id}"}
                    }
                ]
            }
            
            await set_cache(key, json.dumps(mock_data), ttl=LATEST_STORIES_CACHE_TTL)
        
        print(f"Background update completed for {category}:{publishers}")
        
    except Exception as e:
        print(f"Background update failed for {category}:{publishers}: {e}")

def _cleanup_completed_tasks():
    """
    清理已完成的背景任務
    """
    global _background_update_tasks
    completed_keys = [key for key, task in _background_update_tasks.items() if task.done()]
    for key in completed_keys:
        del _background_update_tasks[key]

async def _process_stories_data(
    cache_data: Dict[str, Any], 
    index: int, 
    take: int, 
    start_time: datetime
) -> Dict[str, Any]:
    """
    處理和組織故事數據
    """
    values = cache_data.get("values", [])
    values_filtered = [dict(json.loads(value)) for value in values if value is not None] if values is not None else []
    
    all_stories = []
    update_time = 0
    
    for value in values_filtered:
        update_time = value.get('update_time', 0) if update_time < value.get('update_time', 0) else update_time
        stories = value.get('data', [])
        for story in stories:
            published_date = story['published_date']
            try:
                published_timestamp = int(datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
            except ValueError:
                # 處理不同的日期格式
                try:
                    published_timestamp = int(datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%SZ").timestamp())
                except ValueError:
                    published_timestamp = int(datetime.now().timestamp())
            
            story['published_timestamp'] = published_timestamp
            all_stories.append(story)
    
    # 排序和分頁
    all_stories = sorted(all_stories, key=lambda x: x['published_timestamp'], reverse=True)
    all_stories_pagination = all_stories[index: index + take]
    
    # 計算過期時間
    expire_time = update_time + LATEST_STORIES_EXPIRE_TIME
    
    response = {
        "update_time": update_time,
        "expire_time": expire_time,
        "num_stories": len(all_stories),
        "stories": all_stories_pagination,
        "cache_info": {
            "cache_ttl": LATEST_STORIES_CACHE_TTL,
            "expire_time_seconds": LATEST_STORIES_EXPIRE_TIME,
            "background_update_enabled": LATEST_STORIES_BACKGROUND_UPDATE
        }
    }
    
    # 記錄效能資訊
    end_time = datetime.now()
    send_performance_logging({
        "function": "latest_stories_optimized",
        "stages": [
            {
                "name": "total_processing",
                "start_time": str(start_time),
                "end_time": str(end_time),
                "duration": (end_time - start_time).total_seconds()
            }
        ]
    })
    
    return response

async def force_update_stories(publishers: List[str], category: str):
    """
    強制更新故事數據（管理員功能）
    """
    prefix = FastAPICache.get_prefix()
    await _background_update_stories(publishers, category, prefix)

async def get_cache_status(publishers: List[str], category: str) -> Dict[str, Any]:
    """
    獲取快取狀態資訊
    """
    prefix = FastAPICache.get_prefix()
    cache_data = await _get_cached_stories(publishers, category, prefix)
    
    status_info = {
        "publishers": publishers,
        "category": category,
        "cache_keys": cache_data["keys"],
        "cache_status": [],
        "background_tasks": list(_background_update_tasks.keys()),
        "config": {
            "cache_ttl": LATEST_STORIES_CACHE_TTL,
            "expire_time": LATEST_STORIES_EXPIRE_TIME,
            "background_update_enabled": LATEST_STORIES_BACKGROUND_UPDATE
        }
    }
    
    current_time = datetime.now().timestamp()
    for i, value in enumerate(cache_data["values"]):
        key = cache_data["keys"][i]
        if value is None:
            status_info["cache_status"].append({
                "key": key,
                "status": "missing",
                "age": None
            })
        else:
            try:
                data = json.loads(value)
                update_time = data.get('update_time', 0)
                age = current_time - update_time
                expire_time = update_time + LATEST_STORIES_EXPIRE_TIME
                is_expired = current_time > expire_time
                
                status_info["cache_status"].append({
                    "key": key,
                    "status": "expired" if is_expired else "valid",
                    "age": age,
                    "update_time": update_time,
                    "expire_time": expire_time
                })
            except (json.JSONDecodeError, KeyError):
                status_info["cache_status"].append({
                    "key": key,
                    "status": "corrupted",
                    "age": None
                })
    
    return status_info 