from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class MovieRank(BaseModel):
  rank: int = Field(
    title="Film Rank",
    description="film ranking in list",
    examples=[1]
  )
  film_id: str = Field(
    title="Film ID",
    description="film numerical id extracted from parent list",
    examples=["111490"]
  )
  rating: float | None = Field(
    default=None,
    title="letterboxd film rating using standard algorithm",
    examples=[4.19, 3.44, 4.01]
  )
  classic_rating: float | None
  review_count: int | None = None
  rating_count: int | None = None
  watch_count: int | None = None
  list_appearance_count: int | None = None
  like_count: int | None = None

  model_config = {
    "json_schema_extra": {
      "examples": [
        {
          "rank": 1,
          "film_id": "111490",
          "rating": 4.19,
          "classic_rating": 4.40,
          "review_count": 3440,
          "rating_count": 5032,
          "watch_count": 10403,
          "list_appearance_count": 4500,
          "like_count": 600
        }
      ]
    }
  }

class Movie(BaseModel):
  film_id: str | None = Field(
    default=None,
    title="film numerical id extracted from parent list",
    examples=["111490"]
    )
  film_slug: str | None = Field(
    default=None,
    title="film_title denoted in snake_case form",
    examples=["v-for-vendetta"]
  )
  film_title: str | None = Field(
    default=None,
    title="film title without any string manipulations",
    examples=["V For Vendetta"]
  )
  year: Optional[int] = Field(
    default=None,
    title="release year of film",
    examples=[2007]
  )
  genre: Optional[list[str]] = None
  runtime: Optional[int] = None
  cast: Optional[list[str]] = None
  producers: Optional[list[str]] = None
  production_company: Optional[list[str]] = None
  director: Optional[list[str]] = None
  writer: Optional[list[str]] = None
  writers: Optional[list[str]] = None
  editor: Optional[list[str]] = None
  cinematography: Optional[list[str]] = None
  assistant_director: Optional[list[str]] = None
  production_design: Optional[list[str]] = None
  art_direction: Optional[list[str]] = None
  sound: Optional[list[str]] = None
  poster: Optional[str] = None
  
  model_config = {
    "json_schema_extra": {
      "examples": [
        {
          "film_id": "111490",
          "film_slug": "v-for-vendetta",
          "film_title": "V for Vendetta",
          "year": 2005,
          "genre": [
            "Thriller",
            "Science Fiction"
            "Action"
          ],
          "runtime": 132,
          "cast": ["Natalie Portman", "Hugo Weaving", "Stephen Rea", "Stephen Fry"],
          "producers": ["Joel Silver", "Grant Hill", "Andy Wachowski", "Lana Wachowski"],
          "production_company": ["Warner Bros.", "Virtual Studios", "Silver Pictures", "Anarchos Productions"],
          "director": ["James McTeigue"],
          "writer": ["Lana Wachowski", "Lilly Wachowski"],
          "editor": ["Martin Walsh"],
          "cinematography": ["Adrian Biddle"],
          "assistant_director": ["Kim Armitage", "Basil Grillo", "Tina Maskell", "Ben Dixon"],
          "production_design": ["Owen Paterson"],
          "art_direction": ["James Foster", "Tom Brown", "Steven Lawrence"],
          "sound": ["David Evans", "David Franklin", "Jed M. Dodge", "Hugo Adams", "Patrick Cullen"],
          "poster": "https://a.ltrbxd.com/resized/film-poster/2/6/7/2/3/1/267231-on-north-diversion-road-0-230-0-345-crop.jpg?v=7bcc290517"
        }
      ]
    }
  }

class MovieHistory(Movie):
  movie_history_id: UUID = Field(
    alias="_id",
    description = "id field",
    examples = ["b6db44ea-16e4-4503-8ea9-19b3d53a5772"]
  )
  rating: Optional[float] = Field(
    default=None,
    title="film rating",
    examples=[4.13]
  )
  classic_rating: Optional[float] = None
  review_count: Optional[int] = None
  rating_count: Optional[int] = None
  watch_count: Optional[int] = None
  list_appearance_count: Optional[int] = None
  like_count: Optional[int] = None
  created_at: datetime = Field(
    title="timestamp of movie_history doc creation",
    examples=['2020-12-02T13:32:32.647000']
  )

  model_config = {
    "json_schema_extra": {
      "examples": [
        {
          "film_id": "111490",
          "film_slug": "v-for-vendetta",
          "film_title": "V for Vendetta",
          "year": 2005,
          "genre": [
            "Thriller",
            "Science Fiction"
            "Action"
          ],
          "runtime": 132,
          "cast": ["Natalie Portman", "Hugo Weaving", "Stephen Rea", "Stephen Fry"],
          "producers": ["Joel Silver", "Grant Hill", "Andy Wachowski", "Lana Wachowski"],
          "production_company": ["Warner Bros.", "Virtual Studios", "Silver Pictures", "Anarchos Productions"],
          "director": ["James McTeigue"],
          "writer": ["Lana Wachowski", "Lilly Wachowski"],
          "editor": ["Martin Walsh"],
          "cinematography": ["Adrian Biddle"],
          "assistant_director": ["Kim Armitage", "Basil Grillo", "Tina Maskell", "Ben Dixon"],
          "production_design": ["Owen Paterson"],
          "art_direction": ["James Foster", "Tom Brown", "Steven Lawrence"],
          "sound": ["David Evans", "David Franklin", "Jed M. Dodge", "Hugo Adams", "Patrick Cullen"],
          "poster": "https://a.ltrbxd.com/resized/film-poster/2/6/7/2/3/1/267231-on-north-diversion-road-0-230-0-345-crop.jpg?v=7bcc290517",
          "rating": 4.19,
          "classic_rating": 4.40,
          "review_count": 3440,
          "rating_count": 5032,
          "watch_count": 10403,
          "list_appearance_count": 4500,
          "like_count": 600,
        }
      ]
    }
  }

class MovieOut(BaseModel):
  data: Movie

class MovieHistoryOut(BaseModel):
  data: MovieHistory