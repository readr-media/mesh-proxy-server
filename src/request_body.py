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
  
class SocialPage(BaseModel):
  member_id: str
  index: int
  take: int
  @field_validator('index', 'take')
  @classmethod
  def category_rules(cls, v: int):
    if v < 0:
      raise ValidationError('Invalid input. index and take should not be negative.')
    return v
  
class Search(BaseModel):
  text: str
  objectives: list[str]
  @field_validator('text')
  @classmethod
  def search_rules(cls, v: str):
    if len(v) == 0:
      raise ValidationError('Invalid input. search_text should not be empty.')
    return v
  
  @field_validator('objectives')
  @classmethod
  def objective_rules(cls, v: list[str]):
    if len(v) == 0:
      raise ValidationError('Invalid input. Objective should not be empty.')
    for obj in v:
      if obj not in config.VALID_SEARCH_OBJECTIVES:
        raise ValidationError(f'Invalid input. With invalid objective.')
    return v
  
class Notification(BaseModel):
  memberId: str
  index: int = config.NOTIFY_INDEX
  take: int = config.NOTIFY_TAKE_NUM
  manual: bool = False  
  @field_validator('index', 'take')
  @classmethod
  def take_rules(cls, v: int):
    if v < 0:
      raise ValidationError('Invalid input. index and take should not be negative.')
    return v