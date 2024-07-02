from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from models.movie_data import Movie, MovieRank

class ListHistory(BaseModel):
  history_id: UUID = Field(
    alias="_id", # NOTE: putting alias ensures that _id is represented in docs; normally returns NameError w/o it
    description = "id field",
    examples = ["b6db44ea-16e4-4503-8ea9-19b3d53a5772"]
  )
  list_id: str = Field(
    description = "id field from letterboxd",
    examples = ["22265047"]
  )
  list_name: str = Field(
    examples = ["Top 250 Filipino Movies of Letterboxd"]
  )
  total_pages: int = Field(
    examples=[3]
  )
  data: list[MovieRank] # add list[combined movierank and movie]
  publish_date: datetime = Field(
    description = "Date when list was previously published",
    examples=["2020-12-02T13:32:32.647000"]
  )
  last_update: datetime = Field(
    description = "Date when list was previously updated",
    examples=["2020-12-02T13:32:32.647000"]
  )
  created_at: datetime = Field(
    description ="metadata for when document was recorded",
    examples=["2020-12-02T13:32:32.647000"]
  )

