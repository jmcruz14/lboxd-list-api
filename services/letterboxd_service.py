from typing import Dict, Any, List
import uuid
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from bson.binary import Binary

from .scraper_service import ScraperService
from .list_service import ListService
from obj.list import LetterboxdList
from scripts import getExtraPages, strip_tz, getRankPlacement
from routers.dbconnect import update_db

class LetterboxdService:
  """Main service orchestrating Letterboxd operations"""
  
  def __init__(self, db):
      self.db = db
      self.scraper_service = ScraperService(db)
      self.list_service = ListService(db)
      self.lboxd_url = 'https://letterboxd.com'
      # TODO: Make this configurable instead of hardcoded
      self.lboxd_list_link = 'https://letterboxd.com/tuesjays/list/top-250-narrative-feature-length-filipino/'
      self.lboxd_list_id = '15294077'
  
  async def scrape_letterboxd_list(
      self, 
      list_slug: str, 
      parse_extra_pages: bool = True, 
      film_parse_limit: int = None
  ) -> Dict[str, Any]:
      """Main method to scrape a Letterboxd list"""
      
      # Check database connection
      try:
          await self.db.command('ping')
      except Exception:
          raise Exception("Database connection error")
      
      # Get list metadata
      page = requests.get(self.lboxd_list_link)
      soup = BeautifulSoup(page.content, 'lxml')
      
      list_object = LetterboxdList(soup)
      list_metadata = {
          'list_name': list_object.list_name,
          'publish_date': list_object.publish_date,
          'last_update': list_object.last_update,
          'total_pages': list_object.total_pages
      }
      
      # Check if we need to scrape (compare with existing data)
      existing_list = await self.list_service.get_latest_list_by_id(self.lboxd_list_id)
      
      if existing_list and existing_list['last_update'] == list_metadata['last_update']:
          return existing_list
      
      # Proceed with scraping
      history_id = uuid.uuid4()
      created_at = strip_tz(datetime.now(timezone.utc))
      
      # Process films from main page
      films = await self._process_list_page(soup, film_parse_limit, history_id)
      
      # Process additional pages if requested
      if parse_extra_pages:
          extra_pages = getExtraPages(soup)
          if extra_pages:
              additional_films = await self._process_extra_pages(
                  extra_pages, film_parse_limit, history_id
              )
              films.extend(additional_films)
      
      # Prepare final list data
      list_history = {
          "_id": history_id,
          "list_id": self.lboxd_list_id,
          "created_at": created_at,
          "data": films,
          **list_metadata
      }
      
      # Save to database
      await self._save_list_history(list_history)
      
      return list_history
  
  async def _process_list_page(
      self, 
      soup: BeautifulSoup, 
      film_parse_limit: int, 
      history_id: uuid.UUID
  ) -> List[Dict[str, Any]]:
      """Process films from a single list page"""
      results = soup.find_all('li', 'poster-container', limit=film_parse_limit)
      films = []
      
      for result in results:
          rank_placement = getRankPlacement(result)
          film_poster = result.find('div', 'film-poster')
          
          film = await self.scraper_service.process_film_from_list(
              film_poster, rank_placement, history_id
          )
          films.append(film)
      
      return films
  
  async def _process_extra_pages(
      self, 
      extra_pages: List[str], 
      film_parse_limit: int, 
      history_id: uuid.UUID
  ) -> List[Dict[str, Any]]:
      """Process films from additional pages"""
      films = []
      
      for page_url in extra_pages:
          html_page = requests.get(self.lboxd_url + page_url)
          soup = BeautifulSoup(html_page.content, 'lxml')
          
          page_films = await self._process_list_page(soup, film_parse_limit, history_id)
          films.extend(page_films)
      
      return films
  
  async def _save_list_history(self, list_history: Dict[str, Any]):
      """Save list history to database"""
      save_list = {
          **list_history,
          "_id": Binary.from_uuid(list_history["_id"])
      }
      await update_db(self.db, save_list, 'list_history')
