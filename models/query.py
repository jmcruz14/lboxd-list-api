from hashlib import sha512
from pydantic import BaseModel

class MovieStatsQuery(BaseModel):
  query: list[dict]
  select: list[str] | None = None # select resulting fields OR select all current fields

  # model_config = {
  #   "frozen": True
  # }
  def __hash__(self):
    return int.from_bytes(sha512(f"{self.__class__.__qualname__}::{self.model_dump_json()}".encode('utf-8', errors='ignore')).digest())

class ListStatsQuery(BaseModel):
  pass