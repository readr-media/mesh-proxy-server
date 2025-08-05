import google.cloud.logging as logging
from src.request_body import Search
import os

import asyncio
from concurrent.futures import ThreadPoolExecutor

# 全域執行器用於非同步日誌記錄
_log_executor = ThreadPoolExecutor(max_workers=4)

def send_logging(projectId, logName, info: dict):
    ### writing log
    loggerName = f'projects/{projectId}/logs/{logName}'
    resource = logging.Resource(type='global', labels={'project_id': projectId})
    logger = logging.Client().logger(loggerName)
    logger.log_struct(info = info, severity = "INFO", resource = resource, log_name = loggerName)
    print("Sended logging successed: ", info)

async def send_logging_async(projectId, logName, info: dict):
    """非同步版本的日誌記錄，避免阻塞主執行緒"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_log_executor, send_logging, projectId, logName, info)
    
def send_search_logging(search: Search):
    try:
        projectID = os.environ['PROJECT_ID']
        logName = os.environ['LOG_NAME_SEARCH']
        text, objectives, manual = search.text, search.objectives, search.manual
        if manual==True:
            info = {"text": text, "objectives": objectives}
            send_logging(projectID, logName, info)
    except Exception as e:
        print("send search logging error: ", str(e))
    return
        
def send_performance_logging(data):
    try:
        projectID = os.environ['PROJECT_ID']
        logName = os.environ['LOG_NAME_PERFORMANCE']
        send_logging(projectID, logName, data)
    except Exception as e:
        print("send performance logging error: ", str(e))
    return