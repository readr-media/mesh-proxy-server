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
  publishers: list[str] = []
  category: int
  index: int = config.DEFAULT_LATEST_STORIES_INDEX
  take: int = config.DEFAULT_LATEST_STORIES_TAKE
  
  @field_validator('publishers')
  @classmethod
  def publisher_rules(cls, v: list[str]):
    if len(v)==0:
      raise ValidationError('Invalid input. List of publishers should not be empty.')
    return v
  
  @field_validator('category')
  @classmethod
  def category_rules(cls, v: int):
    if v < 0:
      raise ValidationError('Invalid input. category should greater than 0.')
    return v
  
  @field_validator('index', 'take')
  @classmethod
  def category_rules(cls, v: int):
    if v < 0:
      raise ValidationError('Invalid input. index and take should not be negative.')
    return v