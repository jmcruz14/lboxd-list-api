import os
import json
import asyncio
from typing import Annotated, Any
from fastapi import FastAPI, Request, Body, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from motor.motor_asyncio import AsyncIOMotorClient

from models.movie_data import Movie, MovieOut, MovieHistoryOut
from models.list_history import ListHistory
from models.query import MovieStatsQuery

# from src.constants.query import agg_ops_dict

# from src.scripts.index import getRankPlacement, getExtraPages
from scripts.utils import strip_tz, convert_to_serializable, strip_descriptive_stats

from dbconnect import connect_server, query_db, query_db_agg, update_db

from api.router.dev_only import router as dev_router

# Saved app variable will be run in the shell script
app = FastAPI(
  title="LetterboxdListDashboardAPI",
  version="0.3.2",
  lifespan=connect_server
)
origins = [
  "https://localhost:3000",
  "http://localhost:3000",
  "https://top-250-website.vercel.app/"
]
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

lboxd_url = 'https://letterboxd.com'
lboxd_list_link = 'https://letterboxd.com/tuesjays/list/top-250-narrative-feature-length-filipino/'
lboxd_list_id = '15294077'

async def get_database() -> AsyncIOMotorClient:
  return app.database

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
  print(f"{repr(exc)}")
  return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

# Return a Redirect Response for modification
# FastAPI is a subclass of Starlette
@app.get('/', include_in_schema=False)
async def add(request: Request, status_code=300):
  redirect_url = request.url_for('scrape_letterboxd_list', list_slug='top-250-narrative-feature-length-filipino')
  return RedirectResponse(redirect_url)

@app.get('/movie/fetch/{id}', tags=['movie'], summary="Fetch movie in db", response_model_exclude_none=True)
async def fetch_movie(
  id: int | str, 
  db: AsyncIOMotorClient = Depends(get_database)
) -> MovieOut:
  try:
    await db.command('ping')
  except Exception:
    # client = await connect_server()
    raise HTTPException(status_code=500, detail="Database connection error")

  query = { '_id': { '$eq': str(id) }}
  movie_data = await query_db(db, query, 'movie')
  return MovieOut(data=movie_data[0])

@app.get('/movie_history/fetch/{id}', tags=['movie'], summary="Fetch movie_history in db")
async def fetch_movie_history(
  id: int | str, 
  db: AsyncIOMotorClient = Depends(get_database)
) -> MovieHistoryOut:
  try:
      await db.command('ping')
  except Exception as e:
      raise HTTPException(status_code=500, detail="Database connection error")

  query = { 'film_id': { '$eq': str(id) }}
  results = await query_db(db, query, 'movie_history')

  if not results:
        raise HTTPException(status_code=404, detail="Movie history not found")

  return MovieHistoryOut(data=results[0])

@app.patch('/movie/{film_slug}', response_model=None, tags=['movie'], summary="Patch existing film from DB")
def update_movie(film_slug: str) -> Movie:
  # TODO: update movie metadata here
  return

# @app.get('/list-stats', tags=['letterboxd-list'], summary="Fetch list stats for list history instance")
# async def fetch_list_stat(
#   db: Annotated[AsyncIOMotorClient, Depends(get_database)]
# ):
  # return response based on request body
  # NOTE: for querying in list_history -> agg pipeline should be used
  # parameters:
  # - unwind the data field
  # try:
  #   await db.command('ping')
  # except Exception as e:
  #   raise HTTPException(status_code=500, detail="Database connection error")
  
  # pipeline = [
  #   {
  #     "$unwind": "$data"
  #   }
  # ]

  # result = await query_db_agg(db, pipeline, 'list_history', 1)
  # return {
  #   "data": result,
  #   "length": len(result)
  # }

  # pass

@app.post('/movie-stats', tags=['movie'], summary="Fetch single film stat across entire DB")
async def fetch_film_stat(
    stat: MovieStatsQuery,
    # getCount: Annotated[bool, Query()] = None,
    db: Annotated[AsyncIOMotorClient, Depends(get_database)] = None
  ):
  try:
    await db.command('ping')
  except Exception as e:
    raise HTTPException(status_code=500, detail="Database connection error")
  
  available_keys = Movie.model_fields.keys()
  stat = stat.model_dump()
  queries = stat['query']
  # agg_func = stat['agg_func'] if stat['agg_func'] is not None else None

  # ex: cast = Christopher de Leon; director = Ishmael Bernal
  pipeline = []
  for query in queries:
    # TODO; update by restricting supported key functions
    # if query['field'] not in available_keys:
    #   return HTTPException(status_code=400, detail=f"{stat} key not in model")
    # if query['field'] in ['film_id', 'film_slug', 'film_title']:
    #   return HTTPException(status_code=403, detail="Selected key not permitted for fetching")
    # if query['eq'] is None:
    #   raise HTTPException(status_code=406, detail="Equal value must be not null")

    pipeline.append(query)
  
  result = await query_db_agg(db, pipeline, 'movie', 100)
  return {
    "data": result,
    "length": len(result),
  }

@app.get('/list-history', tags=['letterboxd-list'], summary="Fetch stored list-history item")
async def parse_list(id: int, db: Annotated[AsyncIOMotorClient, Depends(get_database)], fetch_movies: bool = False) -> ListHistory:
  try:
      await db.command('ping')
  except Exception as e:
      raise HTTPException(status_code=500, detail="Database connection error")

  pipeline = [
    { '$match': {'list_id': { '$eq': str(id) }} },
    { '$sort': { 'last_update': -1 } }
  ]
  
  list_history = await query_db_agg(db, pipeline, 'list_history', 1)
  results = convert_to_serializable(list_history[0])
  
  if fetch_movies:
    data = results['data']
    tasks = [
      show_full_data(film, db) for film in data
    ]
    updated_films = await asyncio.gather(*tasks)
    results['data'] = updated_films
    return results
  else:
    return results

app.include_router(dev_router)

async def show_full_data(film, client):
  film_data = await fetch_movie_history(film['film_id'], client)
  try:
    del film_data['_id']
  except KeyError:
    pass
  updated_film = {
    **film,
    **film_data
  }
  return updated_film
