import json
import requests
import re
from bs4 import BeautifulSoup, Tag
from pydantic import ValidationError

from models.movie_data import Movie

from scripts import getClassicHistogramRating, not_numeric, replaceMultipleStrings

from constants.url import fetchStatsUrl, fetchRatingHistogramUrl

class LetterboxdFilmPage:
  """
  The Letterboxd film page handles a lazy-loaded DOM when scraped using BeautifulSoup
  This is different from the DOM shown on inspecting the page via browser.

  The data parsed here pertains to the content seen at the topmost portion
  of the page, from the film title to the runtime. It does not cover
  friend activity or reviews.

  Attributes
  ----------
  filmHeader: bs4.Tag
    the film's header element of the Soup object
  filmBody: bs4.Tag
    the film's content element of the Soup object
  filmFooter: bs4.Tag
    the film's footer element of the Soup object

  Methods
  ----------
  getFilmTitle():
    obtains film title
  getReleaseYear():
    obtains film release year
  getCastData():
    obtains film cast data
  getCrewData():
    obtains crew data
  getGenre():
    obtains film genre/s
  getRuntime():
    obtains film runtime
  """

  def __init__(self, soup: BeautifulSoup):
    self.filmHeader = soup.find('section', ['film-header-group'])
    self.filmBody = soup.find('div', id='tabbed-content')
    self.filmFooter = soup.find('p', ['text-link', 'text-footer'])
    self.contentNav = soup.find('div', id='content-nav')
    self.soup = soup
    # print(soup)
    # TODO: explore instantiating metadata on initialization

    # get pertinent data if enabled
  
  def getScript(self, soup):
    scriptContent = soup.find('script', type='application/ld+json')
    script = scriptContent.text.split('*/')[1].split('/*')[0]
    self.script = json.loads(script)
  
  def getStats(self, film_slug: str):
    '''
      The stats data is retrieved from a different endpoint (/csi/film/{movie}/stats)
      before it is loaded onto the resulting page. 
    '''
    self.statsUrl = fetchStatsUrl(film_slug)
    statsRequest = requests.get(self.statsUrl)
    statsSoup = BeautifulSoup(statsRequest.content, 'lxml')
    self.watchCount = int(re.sub(not_numeric, '', statsSoup.find('li', 'filmstat-watches').a.get('title')))
    self.listAppCount = int(re.sub(not_numeric, '', statsSoup.find('li', 'filmstat-lists').a.get('title')))
    self.likeCount = int(re.sub(not_numeric, '', statsSoup.find('li', 'filmstat-likes').a.get('title')))

    return {
      'watch_count': self.watchCount,
      'list_appearance_count': self.listAppCount,
      'like_count': self.likeCount,
    }

  def getRating(self) -> int|float | None:
    try:
      # handle error IF aggregate rating is not found
      json_script = self.script
      if 'aggregateRating' in json_script:
        aggregateRating = json_script['aggregateRating']
        ratingValue = aggregateRating['ratingValue']
        return ratingValue
      else:
        # perform classic rating algorithm here?
        # or just keep it separate?
        raise Exception
    except Exception as e:
      print(f"Error occurred while parsing rating: {e}")
      return None
  
  def getClassicRating(self) -> int|float | None:
    try:
      hist_url = fetchRatingHistogramUrl(self.film_slug)
      histRequest = requests.get(hist_url)
      histSoup = BeautifulSoup(histRequest.content, 'lxml')
      histogram_rating = getClassicHistogramRating(histSoup)
      
      return histogram_rating
    except Exception as e:
      print(f"Error occurred while parsing histogram rating: {e}")
      return None
  
  def getReviewCount(self) -> None:
    try:
      json_script = self.script
      aggregateRating = json_script['aggregateRating']
      reviewCount = aggregateRating['reviewCount']
      return reviewCount
    except Exception as e:
      print(f"Error occurred while parsing review count: {e}")
      reviewCount = None
      return reviewCount

  def getRatingCount(self) -> None:
    try:
      # handle error IF aggregate rating is not found
      json_script = self.script
      aggregateRating = json_script['aggregateRating']
      ratingCount = aggregateRating['ratingCount']

      return ratingCount
    except Exception as e:
      print(f"Error occurred while parsing rating count: {e}")
      ratingCount = None
      
      return ratingCount

  def getFilmTitle(self: Tag) -> str:
    try:
      return self.filmHeader.find('h1').get_text()
    
    except Exception as e:
      print(f"Error occurred while parsing film title: {e}")
      return ''
  
  def getProductionCompany(self: Tag) -> list[str]:
    try:
      return list(map(lambda x: x['name'], self.script['productionCompany']))
    except Exception as e:
      print(f"Error occurred while parsing production company: {e}")
      return None
  
  def getReleaseYear(self: Tag) -> int:
    try:
      elem = self.filmHeader.find('div', ['releaseyear'])
      year = int(elem.text) if elem else None
      return year
    
    except Exception as e:
      print(f"Error occurred while parsing release year: {e}")
      return ''

  def getCastData(self: Tag) -> list[str]:
    try:
      cast_list = self.filmBody.find('div', 'cast-list').p
      cast  = [cast.text for cast in cast_list.find_all('a', 'text-slug') if cast.text.strip() or cast.text.strip() != 'Show All…']
      return cast
    except Exception as e:
      print(f"Error occurred while parsing cast members: {e}")
      return ['']
  
  def getCrewData(self: Tag) -> dict:
    crew_ = {}
    crew_div = self.filmBody.find('div', '-crewroles')
    if crew_div:
      crewroles = crew_div.find_all('h3')
      for role in crewroles:
        category = role.find('span', ['crewrole', '-full'])
        category_text = category.text.replace(' ', '_').lower()
        category_sibling = role.find_next_sibling('div')
        if category_sibling:
          role_owners = [role_owner.get_text().strip() for role_owner in category_sibling.p if role_owner.text.strip()]
          crew_[category_text] = role_owners
        else:
          crew_[category_text] = None
    return crew_

  def getGenre(self: Tag) -> list[str]:

    def genre_filter(tag):
      return tag.name == 'a' and 'text-slug' in tag.get('class', []) and tag.get('href').startswith('/films/genre')

    try:
      genres_tab = self.filmBody.find('div', {'id':'tab-genres'})
      genres_list = genres_tab.find_all(genre_filter)
      genres_ = [genre.get_text().strip() for genre in genres_list]
      return genres_
    except Exception as e:
      print(f"Error occurred while parsing genre: {e}")
      return ['']
  
  def getRuntime(self: Tag) -> int | None:
    try:
      genre_text = [replaceMultipleStrings(char) for char in self.filmFooter.stripped_strings]
      assert 'mins' in genre_text[0]
      mins_str = genre_text[0]
      mins_ = int(genre_text[0][:mins_str.index('mins')])
      return mins_
      # return genre_text[mins_ - 1]
    except Exception as e:
      print(f"Error occurred while parsing runtime: {e}")
      return None
  
  def getPoster(self: Tag) -> str | None:
    try:
      json_script = self.script
      image = json_script['image']

      return image
    except Exception as e:
      print(f"Error occurred while parsing rating count: {e}")
      image = None
      
      return image
  
  def getAllStats(self):
    self.getScript(self.soup)
    self.film_slug = self.script['url'].split('/')[4]
    self.film_title = self.getFilmTitle()
    self.production_company = self.getProductionCompany()
    self.release_year = self.getReleaseYear()
    self.genres = self.getGenre()
    self.cast = self.getCastData()
    self.crew = self.getCrewData()
    self.rating = self.getRating()
    self.classic_rating = self.getClassicRating()
    self.stats_data = self.getStats(self.film_slug)
    self.review_count = self.getReviewCount()
    self.rating_count = self.getRatingCount()
    self.runtime = self.getRuntime()
    self.poster = self.getPoster()

    return {
      'film_slug': self.film_slug,
      'film_title': self.film_title,
      'year': self.release_year,
      'rating': self.rating,
      'classic_rating': self.classic_rating,
      'review_count': self.review_count,
      'rating_count': self.rating_count,
      **self.stats_data,
      'genre': self.genres,
      'runtime': self.runtime,
      'cast': self.cast,
      'production_company': self.production_company,
      **self.crew,
      'poster': self.poster
    }
  
  def validate_model(self, dict):
    json_model = json.dumps(dict)
    try:
      instance = Movie.model_validate_json(json_model)
      assert instance
    except ValidationError as e:
      print("Validation failed", e)

if __loader__.name == '__main__':
    import sys
    sys.path.append(sys.path[0] + '/..')