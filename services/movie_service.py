from typing import Dict, Any
from pymongo import AsyncMongoClient
from routers.dbconnect import query_db

class MovieService:
  """Service layer for movie-related operations"""
  
  def __init__(self, db: AsyncMongoClient):
    self.db = db
  
  async def get_movie_by_id(self, movie_id: str):
    """Get movie data by ID"""
    try:
        await self.db.command('ping')
    except Exception:
        raise Exception("Database connection error")

    query = {'_id': {'$eq': str(movie_id)}}
    movie_data = await query_db(self.db, query, 'movie')
    
    if not movie_data:
        return None
        
    return movie_data[0]
  
  async def get_movie_history_by_film_id(self, film_id: str):
    """Get movie history data by film ID"""
    try:
        await self.db.command('ping')
    except Exception:
        raise Exception("Database connection error")

    query = {'film_id': {'$eq': str(film_id)}}
    results = await query_db(self.db, query, 'movie_history')

    if not results:
        return None

    return results[0]
