import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
# 確保 JSON 優化生效
import src.json_optimizer
import json
import os
from contextlib import asynccontextmanager

class PerformanceMonitor:
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.stages = {}
        self.start_time = None
        self.end_time = None
        
    def start(self):
        """開始監控"""
        self.start_time = time.time()
        self.stages = {}
        
    def add_stage(self, stage_name: str, duration: float, metadata: Optional[Dict] = None):
        """添加一個執行階段"""
        self.stages[stage_name] = {
            "duration": duration,
            "metadata": metadata or {}
        }
        
    def end(self):
        """結束監控"""
        self.end_time = time.time()
        
    def get_total_duration(self) -> float:
        """取得總執行時間"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
        
    def get_summary(self) -> Dict[str, Any]:
        """取得監控摘要"""
        return {
            "endpoint": self.endpoint_name,
            "total_duration": self.get_total_duration(),
            "stages": self.stages,
            "timestamp": datetime.now().isoformat()
        }

@asynccontextmanager
async def monitor_stage(monitor: PerformanceMonitor, stage_name: str):
    """非同步上下文管理器，用於監控單個階段"""
    stage_start = time.time()
    try:
        yield
    finally:
        stage_duration = time.time() - stage_start
        monitor.add_stage(stage_name, stage_duration)

async def log_performance_detailed_async(monitor: PerformanceMonitor):
    """非同步記錄詳細的效能資訊"""
    try:
        projectID = os.environ.get('PROJECT_ID')
        logName = os.environ.get('LOG_NAME_PERFORMANCE', 'performance')
        
        if projectID:
            from src.log import send_logging_async
            await send_logging_async(projectID, logName, monitor.get_summary())
        else:
            # 如果沒有設定 Google Cloud Logging，直接印出到 console
            print("=== PERFORMANCE MONITOR ===")
            print(json.dumps(monitor.get_summary(), indent=2, ensure_ascii=False))
            print("===========================")
            
    except Exception as e:
        print(f"Performance logging error: {e}")

def log_performance_detailed(monitor: PerformanceMonitor):
    """同步版本的效能記錄（向後相容）"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已經在事件迴圈中，建立一個任務
            asyncio.create_task(log_performance_detailed_async(monitor))
        else:
            # 如果不在事件迴圈中，直接執行
            loop.run_until_complete(log_performance_detailed_async(monitor))
    except RuntimeError:
        # 如果沒有事件迴圈，使用同步版本
        try:
            projectID = os.environ.get('PROJECT_ID')
            logName = os.environ.get('LOG_NAME_PERFORMANCE', 'performance')
            
            if projectID:
                from src.log import send_logging
                send_logging(projectID, logName, monitor.get_summary())
            else:
                print("=== PERFORMANCE MONITOR ===")
                print(json.dumps(monitor.get_summary(), indent=2, ensure_ascii=False))
                print("===========================")
        except Exception as e:
            print(f"Performance logging error: {e}")

# 全域效能監控實例
_current_monitor: Optional[PerformanceMonitor] = None

def get_current_monitor() -> Optional[PerformanceMonitor]:
    return _current_monitor

def set_current_monitor(monitor: PerformanceMonitor):
    global _current_monitor
    _current_monitor = monitor 