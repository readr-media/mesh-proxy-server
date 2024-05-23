from pydantic import BaseModel, ConfigDict
from typing import Optional

class GqlQuery(BaseModel):
  model_config = ConfigDict(extra='allow')
  query: str
  operationName: Optional[str] = None
  variables: Optional[dict] = None

class JsonQuery(BaseModel):
  model_config = ConfigDict(extra='allow')

class LatestStories(BaseModel):
  publishers: list[str] = []