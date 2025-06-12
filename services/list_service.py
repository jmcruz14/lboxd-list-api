import asyncio
from typing import List, Dict, Any
from pymongo import AsyncMongoClient
from scripts import convert_to_serializable
from routers.dbconnect import query_db_agg

class ListService:
  """
   Service layer for list-related operations.
  """

  def __init__(self, db: AsyncMongoClient):
    self.db = db

  async def get_latest_list_by_id(self, list_id: str, fetch_movies: bool = False) -> Dict[str, Any]:
    """
      Get the most recent list history entry for a given list by ID
    """

    try:
      await self.db.command('ping')
    except Exception: # improve exception here
      raise Exception("Database connection error")

    pipeline = [
      {'$match': {'list_id': {'$eq': str(list_id)}}},
      {'$sort': {'last_update': -1}}
    ]
        
    list_history = await query_db_agg(self.db, pipeline, 'list_history', 1)
    
    if not list_history:
      return None
        
    result = convert_to_serializable(list_history[0])
        
    # If fetch_movies is True, enrich the film data with full movie history
    if fetch_movies:
        result = await self._enrich_with_movie_data(result)
        
    return result
  
  async def _enrich_with_movie_data(self, list_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich list data with full movie history information"""
    films = list_data.get('data', [])
    
    # Process all films concurrently
    tasks = [
        self._enrich_single_film(film) for film in films
    ]
    enriched_films = await asyncio.gather(*tasks)
    
    # Update the list data with enriched films
    list_data['data'] = enriched_films
    return list_data
  
  async def _enrich_single_film(self, film: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich a single film with full movie history data"""
    film_id = film.get('film_id')
    if not film_id:
        return film
    
    # Get movie history data
    movie_history = await self.movie_service.get_movie_history_by_film_id(film_id)
    
    if not movie_history:
        return film
    
    # Remove the _id field from movie_history to avoid conflicts
    movie_history_clean = {k: v for k, v in movie_history.items() if k != '_id'}
    
    # Merge film ranking data with movie history data
    enriched_film = {
        **film,
        **movie_history_clean
    }
    
    return enriched_film
