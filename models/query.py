from hashlib import sha512
from pydantic import BaseModel

class AggFuncQuery(BaseModel):
  measure: str
  field: str

class StatQuery(BaseModel):
  field: str
  eq: str | int | bool | None = None
  gt: int | None = None
  lt: int | None = None

class MovieStatsQuery(BaseModel):
  query: list[StatQuery]
  agg_func: AggFuncQuery | None = None
  select: list[str] | None = None

  # model_config = {
  #   "frozen": True
  # }
  def __hash__(self):
    return int.from_bytes(sha512(f"{self.__class__.__qualname__}::{self.model_dump_json()}".encode('utf-8', errors='ignore')).digest())

class ListStatsQuery(BaseModel):
  pass