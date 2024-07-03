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

import requests
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime, timezone
from bson import Binary, decode

from models.movie_data import Movie, MovieOut, MovieHistoryOut
from models.list_history import ListHistory
from models.query import MovieStatsQuery

from obj.list import LetterboxdList
from obj.movie import LetterboxdFilmPage

from constants.query import agg_ops_dict

from scripts.index import getRankPlacement, getExtraPages
from scripts.utils import strip_tz, convert_to_serializable, strip_descriptive_stats

from dbconnect import connect_server, query_db, query_db_agg, update_db

from api.dev_only import router as dev_router

# Saved app variable will be run in the shell script
app = FastAPI(
  title="LetterboxdListDashboardAPI",
  version="0.3.1",
  lifespan=connect_server
)
origins = [
  "https://localhost:3000",
  "http://localhost:3000"
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

# TODO: add OAuth for security
@app.get(
    '/letterboxd-list/{list_slug}',
    tags=['letterboxd-list'],
    summary="Scrape and Fetch Letterboxd List"
  )
async def scrape_letterboxd_list(
  list_slug: str,
  parse_extra_pages: bool = True,
  film_parse_limit: int = None,
  db: AsyncIOMotorClient = Depends(get_database)
) -> ListHistory:
  '''
    Performs a webscraping function to extract data from lazy-loaded DOM
    in Letterboxd.
  '''

  history_id = uuid.uuid4()
  created_at = strip_tz(datetime.now(timezone.utc))
  page = requests.get(lboxd_list_link)
  soup = BeautifulSoup(page.content, 'lxml')
  save_scrape = False

  list_object = LetterboxdList(soup)
  list_name = list_object.list_name
  publish_date = list_object.publish_date
  last_update = list_object.last_update
  total_pages = list_object.total_pages
  pages = getExtraPages(soup)
  results = soup.find_all('li', 'poster-container', limit=film_parse_limit)

  try:
    await db.command('ping')
  except Exception:
    raise HTTPException(status_code=500, detail="Database connection error")

  list_entry = await parse_list(lboxd_list_id, db)
  list_entry_date = list_entry['last_update']
  if list_entry_date == last_update:
    return jsonable_encoder(list_entry)
  else:
    save_scrape = True

  films = []
  
  for result in results:
    rank_placement = getRankPlacement(result)
    film_poster = result.find('div', 'film-poster')
    film_id = film_poster['data-film-id']
    film_slug = film_poster['data-film-slug']

    film = {
      'rank': rank_placement,
      'film_id': film_id,
    }

    query = { '_id': { '$eq': film_id } }
    film_in_db = await query_db(db, query, 'movie')
    # NOTE: explore adding additional flag to check if changes in movie were made
    if not film_in_db:
      print(f"New film detected in list! Parsing film_id: {film_id}")
      result = scrape_movie(film_slug, film_id)
      film_data = result['data']
      film_numerical_stats = {
        'rating': film_data['rating'] if 'rating' in film_data else None,
        'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
        'review_count': film_data['review_count'] if 'review_count' in film_data else None,
        'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
        'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
        'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
        'like_count': film_data['like_count'] if 'like_count' in film_data else None,
      }

      movie_history_id = uuid.uuid4()
      movie_history_created_at = strip_tz(datetime.now(timezone.utc))
      movie_history = {
        **film_data,
        '_id': Binary.from_uuid(movie_history_id),
        'list_id': history_id,
        'film_id': film_id,
        'created_at': movie_history_created_at,
      }
      await update_db(db, movie_history, 'movie_history')
      
      movie = strip_descriptive_stats(film_data)
      await update_db(db, movie, 'movie')

      film = {
        **film,
        **film_numerical_stats
      }
    else:

      # TODO: include a flag in this API to add to movie_history since the list is new
      movie_history_query = { 'film_id': { '$eq': film_id }}
      latest_film = await query_db(db, movie_history_query, 'movie_history')
      film_data = latest_film[0]

      # if save_scrape:
      #   result = scrape_movie(film_slug, film_id)
      #   film_data = result['data']
      #   film_numerical_stats = {
      #     'rating': film_data['rating'] if 'rating' in film_data else None,
      #     'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
      #     'review_count': film_data['review_count'] if 'review_count' in film_data else None,
      #     'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
      #     'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
      #     'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
      #     'like_count': film_data['like_count'] if 'like_count' in film_data else None,
      #   }

      #   movie_history_id = uuid.uuid4()
      #   movie_history_created_at = strip_tz(datetime.now(timezone.utc))
      #   movie_history = {
      #     **film_data,
      #     '_id': Binary.from_uuid(movie_history_id),
      #     'list_id': history_id,
      #     'film_id': film_id,
      #     'created_at': movie_history_created_at,
      #   }
      #   await update_db(db, movie_history, 'movie_history')

      # if save_scrape == True: get

      film_numerical_stats = {
        'rating': film_data['rating'] if 'rating' in film_data else None,
        'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
        'review_count': film_data['review_count'] if 'review_count' in film_data else None,
        'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
        'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
        'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
        'like_count': film_data['like_count'] if 'like_count' in film_data else None,
      }
      film = {
        **film,
        **film_numerical_stats
      }

    films.append(film)

  if pages and parse_extra_pages:
    for page in pages:
      html_page = requests.get(lboxd_url + page)
      soup = BeautifulSoup(html_page.content, 'lxml')
      results = soup.find_all('li', 'poster-container', limit=film_parse_limit)
      for result in results:
        rank_placement = getRankPlacement(result)
        film_poster = result.find('div', 'film-poster')
        film_id = film_poster['data-film-id']
        film_slug = film_poster['data-film-slug']

        film = {
          'rank': rank_placement,
          'film_id': film_id,
        }

        query = { '_id': { '$eq': film_id } }
        film_in_db = await query_db(db, query, 'movie')
        if not film_in_db:
          print(f"New film detected in list! Parsing film_id: {film_id}")
          result = scrape_movie(film_slug, film_id)
          film_data = result['data']
          film_numerical_stats = {
            'rating': film_data['rating'] if 'rating' in film_data else None,
            'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
            'review_count': film_data['review_count'] if 'review_count' in film_data else None,
            'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
            'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
            'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
            'like_count': film_data['like_count'] if 'like_count' in film_data else None,
          }

          movie_history_id = uuid.uuid4()
          movie_history_created_at = strip_tz(datetime.now(timezone.utc))
          movie_history = {
            **film_data,
            '_id': Binary.from_uuid(movie_history_id),
            'list_id': history_id,
            'film_id': film_id,
            'created_at': movie_history_created_at,
          }
          await update_db(db, movie_history, 'movie_history')

          movie = strip_descriptive_stats(film_data)
          await update_db(db, movie, 'movie')
          
          film = {
            **film,
            **film_numerical_stats
          }
        else:
          movie_history_query = { 'film_id': { '$eq': film_id }}
          latest_film = await query_db(db, movie_history_query, 'movie_history')
          film_data = latest_film[0]
          film_numerical_stats = {
            'rating': film_data['rating'] if 'rating' in film_data else None,
            'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
            'review_count': film_data['review_count'] if 'review_count' in film_data else None,
            'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
            'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
            'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
            'like_count': film_data['like_count'] if 'like_count' in film_data else None,
          }
          film = {
            **film,
            **film_numerical_stats
          }
        
        films.append(film)
  
  list_history = {
    "_id": history_id,
    "list_id": lboxd_list_id,
    "list_name": list_name,
    "total_pages": total_pages,
    "data": films, 
    "publish_date": publish_date,
    "last_update": last_update,
    "created_at": created_at
  }

  if save_scrape:
    save_list = {
      "_id": Binary.from_uuid(history_id),
      "list_id": lboxd_list_id,
      "list_name": list_name,
      "total_pages": total_pages,
      "data": films,
      "publish_date": publish_date,
      "last_update": last_update,
      "created_at": created_at
    }
    await update_db(db, save_list, 'list_history')
  db.close()

  return list_history

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

@app.get(
    '/movie/scrape/{film_slug}', 
    tags=['movie'], 
    summary="Scrape movie from list",
    response_model_exclude_none=True
  )
def scrape_movie(
    film_slug: str,
    film_id: int | None = None
  ) -> MovieOut:
  film_base_uri = f"https://letterboxd.com/film/{film_slug}"
  response = requests.get(film_base_uri)
  soup = BeautifulSoup(response.content, 'lxml')
  page = LetterboxdFilmPage(soup)
  film_data = page.getAllStats()
  film = {
    **film_data
  }
  if film_id:
    film = {
      '_id': str(film_id),
      **film
    }
  page.validate_model(film)
  return { 
    'data': film,
  }

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

  query = { 'list_id': { '$eq': str(id) } }
  list_history = await query_db(db, query, 'list_history', 1)
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