from datetime import datetime
from bs4 import BeautifulSoup
from scripts.utils import convert_to_dt

class LetterboxdList:
	def __init__(self, soup: BeautifulSoup) -> None:
		self.list_name = self.getListName(soup)
		self.publish_date = self.getPublishDate(soup)
		self.last_update = self.getLastUpdate(soup)
		self.total_pages = self.getTotalPages(soup)
	
	def getListName(self, soup) -> str:
		try:
			list_name = soup.find('h1', ['title-1', 'prettify'])
			list_name = list_name.get_text()
		except Exception:
			list_name = ''
		return list_name
	
	def getPublishDate(self, soup) -> datetime | None:
		try:
			publish_tag = soup.find('span', 'published')
			publish_time = publish_tag.find('time')
			publish_date = publish_time.get('datetime')
			publish_date = convert_to_dt(publish_date)
		except Exception:
			publish_date = None
		return publish_date
	
	def getLastUpdate(self, soup) -> datetime | None:
		try:
			update_tag = soup.find('span', 'updated')
			update_time = update_tag.find('time')
			last_update = update_time.get('datetime')
			last_update = convert_to_dt(last_update)
		except Exception:
			last_update = None
		return last_update

	def getTotalPages(self, soup) -> int | None:
		try:
			paginate_grp = soup.find('div', 'paginate-pages')
			pages = paginate_grp.find_all('li')
			total_pages = int(pages[-1].text)

		except Exception:
			total_pages = None
		return total_pages
