import re
from uuid import UUID
from base64 import b64encode
from bson import Binary
from datetime import datetime, timezone
from typing import Iterable
from pydantic import BaseModel, create_model

def merge_base_models(name: str, *models: Iterable[BaseModel]) -> BaseModel:
  fields = {}
  for model in models:
        f = {k: (v.annotation, v) for k, v in model.model_fields.items()}
        fields.update(f)
  return create_model(name, **fields)

def convert_to_serializable(d):
  for key, value in d.items():
    if isinstance(value, Binary) and key == '_id':
        uuid_obj = UUID(bytes=value)
        d[key] = str(uuid_obj)
    elif isinstance(value, Binary) and key != '_id':
        d[key] = b64encode(value).decode('utf-8')
  return d

def strip_descriptive_stats(movie_obj: dict) -> dict:
   obj_no_stats = {
      x: movie_obj[x] for x in movie_obj if x not in [
         'rating', 
         'classic_rating', 
         'review_count',
         'rating_count',
         'watch_count',
         'list_appearance_count',
         'like_count'
        ]
   }
   return obj_no_stats

def extract_numeric_text(tag) -> int:
  try:
    return int(re.sub(r"[^0-9]", '', tag))
  except Exception:
    return None

def convert_to_dt(datetime_str: str) -> datetime:
  # Convert string to datetime object
  timestamp_dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")

  return timestamp_dt

def strip_tz(datetime_dt: datetime) -> datetime:
  dt = datetime.fromisoformat(str(datetime_dt))

  # Remove the timezone information
  dt_without_tz = dt.replace(tzinfo=None)

  # Format back to string without the timezone
  cleaned_datetime_str = dt_without_tz.isoformat()
  
  # Return as datetime
  return cleaned_datetime_str

