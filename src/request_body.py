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
  
  @field_validator('publishers')
  @classmethod
  def category_rules(cls, v: list[str]):
    if len(v)==0:
      raise ValidationError('Invalid input. List of publishers should not be empty.')
    return v
  
  @field_validator('category')
  @classmethod
  def index_rules(cls, v: int):
    if v < 0:
      raise ValidationError('Invalid input. Int datatype should not be negative.')
    return v