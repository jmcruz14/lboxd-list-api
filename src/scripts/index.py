'''Module containing all parsing scripts related to BeautifulSoup objects.'''


from bs4 import BeautifulSoup, Tag


# insert a class object here for easier compact use
def getFilmId(tag: Tag) -> str | None:
	try:
		_target = tag.find('div' 'film-watch-link-target')
		return _target['data-film-id']
	except Exception as e:
		print(f"Error occurred while parsing film ID: {e}")
		return None

def getRankPlacement(tag: Tag) -> str:
	rank = int(tag.find('p', 'list-number').get_text())
	return rank

def getExtraPages(soup: BeautifulSoup) -> list:
	try:
			pagination_div = soup.find('div', 'paginate-pages')
			if pagination_div:
					extra_pages = [page_link.find('a')['href'] for page_link in pagination_div.ul.find_all('li') if page_link.find('a')]
					return extra_pages
			else:
					return []
	except Exception as e:
			print(f"Error occurred while parsing extra pages: {e}")
			return []

def getFilmName(film_poster: Tag) -> str:
	try:
		img_el = film_poster.find('img')
		if img_el:
			return img_el['alt']
		else:
			return film_poster['data-film-slug'].replace("-", ' ').title()
	except Exception as e:
		print(f"Error occurred while parsing film name: {e}")
		return ""
