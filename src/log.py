import google.cloud.logging as logging
from src.request_body import Search
import os

def send_logging(projectId, logName, info: dict):
    ### writing log
    loggerName = f'projects/{projectId}/logs/{logName}'
    resource = logging.Resource(type='global', labels={'project_id': projectId})
    logger = logging.Client().logger(loggerName)
    logger.log_struct(info = info, severity = "INFO", resource = resource, log_name = loggerName)
    print("Sended logging successed: ", info)
    
def send_search_logging(search: Search):
    projectID = os.environ['PROJECT_ID']
    logName = os.environ['LOG_NAME_SEARCH']
    text, objectives, manual = search.text, search.objectives, search.manual
    if manual==True:
        info = {"text": text, "objectives": objectives}
        send_logging(projectID, logName, info)