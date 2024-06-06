from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from typing import Optional
import src.config as config 

class GqlQuery(BaseModel):
  model_config = ConfigDict(extra='allow')
  query: str
  operationName: Optional[str] = None
  variables: Optional[dict] = None

class JsonQuery(BaseModel):
  json_payload: bytes
  
class DictQuery(BaseModel):
  model_config = ConfigDict(extra='allow')

class LatestStories(BaseModel):
  categories: list[str] = []
  publishers: list[str] = []
  start_index: int
  num_stories: Optional[int] = config.DEFAULT_LATEST_STORIES_NUM
  
  @field_validator('categories', 'publishers')
  @classmethod
  def category_rules(cls, v: list[str]):
    if len(v)==0:
      raise ValidationError('Invalid input. List of categories and publishers should not be empty.')
    return v
  
  @field_validator('start_index')
  @classmethod
  def index_rules(cls, v: int):
    if v < 0:
      raise ValidationError('Invalid input. Start index should not be negative.')
    return v