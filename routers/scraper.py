from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from services import LetterboxdService
from models import ListHistory
from dependencies import DatabaseDep

lboxd_list_link = 'https://letterboxd.com/tuesjays/list/top-250-narrative-feature-length-filipino/'

scraper_route = APIRouter()

@scraper_route.get(
    '/letterboxd-list/{list_slug}',
    tags=['scraper'],
    summary="Scrape and Fetch Letterboxd List"
  )
async def scrape_letterboxd_list(
  list_slug: str,
  db: DatabaseDep,
  parse_extra_pages: bool = True,
  film_parse_limit: int = None,
) -> ListHistory:
  '''
    Performs a webscraping function to extract data from lazy-loaded DOM
    in Letterboxd.
  '''
  letterboxd_service = LetterboxdService(db)
  try:
    result = await letterboxd_service.scrape_letterboxd_list(
        list_slug, parse_extra_pages, film_parse_limit
    )
    return result
  except Exception as e:
    if "Database connection error" in str(e):
        raise HTTPException(status_code=500, detail="Database connection error")
    raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# @scraper_route.get(
#     '/movie/scrape/{film_slug}', 
#     tags=['scraper'], 
#     summary="Scrape movie from list",
#     response_model_exclude_none=True
#   )
# def scrape_movie(
#     film_slug: str,
#     film_id: int | None = None
#   ) -> MovieOut:
#   film_base_uri = f"https://letterboxd.com/film/{film_slug}"
#   response = requests.get(film_base_uri)
#   soup = BeautifulSoup(response.content, 'lxml')
#   page = LetterboxdFilmPage(soup)
#   film_data = page.getAllStats()
#   film = {
#     **film_data
#   }
#   if film_id:
#     film = {
#       '_id': str(film_id),
#       **film
#     }
#   page.validate_model(film)
#   return { 
#     'data': film,
#   }