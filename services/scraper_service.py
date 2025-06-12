import uuid
import requests
import logging
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from bson.binary import Binary

from obj.movie import LetterboxdFilmPage
from obj.list import LetterboxdList
from scripts.index import getRankPlacement, getExtraPages
from scripts.utils import strip_tz, strip_descriptive_stats
from routers.dbconnect import query_db, update_db

class ScraperService:
  logger = logging.getLogger(__name__)
  """
    Service for scraper-related operations
  """

  def __init__(self, db):
    self.db = db
    self.lboxd_url = 'https://letterboxd.com'

  async def scrape_movie_data(self, film_slug: str, film_id: Optional[str] = None) -> Dict[str, Any]:
    """Scrape movie data from Letterboxd"""
    film_base_uri = f"https://letterboxd.com/film/{film_slug}"
    response = requests.get(film_base_uri)
    soup = BeautifulSoup(response.content, 'lxml')
    page = LetterboxdFilmPage(soup)
    film_data = page.getAllStats()
    
    film = {**film_data}
    if film_id:
        film = {'_id': str(film_id), **film}
    
    page.validate_model(film)
    return film
    
  async def process_film_from_list(self, film_poster, rank_placement: int, history_id: uuid.UUID) -> Dict[str, Any]:
    """Process a single film from a list, handling both new and existing films"""
    film_id = film_poster['data-film-id']
    film_slug = film_poster['data-film-slug']

    film = {
        'rank': rank_placement,
        'film_id': film_id,
    }

    # Check if film exists in database
    query = {'_id': {'$eq': film_id}}
    film_in_db = await query_db(self.db, query, 'movie')
    
    if not film_in_db:
        self.logger.info(f"New film detected in list! Parsing film_id: {film_id}")
        # Scrape new movie data
        film_data = await self.scrape_movie_data(film_slug, film_id)
        
        # Save to movie_history
        await self._save_movie_history(film_data, history_id, film_id)
        
        # Save to movie collection (without numerical stats)
        movie = strip_descriptive_stats(film_data)
        await update_db(self.db, movie, 'movie')
        
        # Extract numerical stats for the film rank
        film.update(self._extract_numerical_stats(film_data))
    else:
        # Get existing film data from movie_history
        movie_history_query = {'film_id': {'$eq': film_id}}
        latest_film = await query_db(self.db, movie_history_query, 'movie_history')
        film_data = latest_film[0]
        film.update(self._extract_numerical_stats(film_data))

    return film
  
  def _extract_numerical_stats(self, film_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract numerical statistics from film data"""
    return {
        'rating': film_data.get('rating'),
        'classic_rating': film_data.get('classic_rating'),
        'review_count': film_data.get('review_count'),
        'rating_count': film_data.get('rating_count'),
        'watch_count': film_data.get('watch_count'),
        'list_appearance_count': film_data.get('list_appearance_count'),
        'like_count': film_data.get('like_count'),
    }
  
  async def _save_movie_history(self, film_data: Dict[str, Any], history_id: uuid.UUID, film_id: str):
    """Save movie data to movie_history collection"""
    movie_history_id = uuid.uuid4()
    movie_history_created_at = strip_tz(datetime.now(timezone.utc))
    movie_history = {
        **film_data,
        '_id': Binary.from_uuid(movie_history_id),
        'list_id': history_id,
        'film_id': film_id,
        'created_at': movie_history_created_at,
    }
    await update_db(self.db, movie_history, 'movie_history')