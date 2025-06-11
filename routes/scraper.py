# from main import get_database
# from fastapi import APIRouter, Depends, Request, Body, Query

# router = APIRouter()

# @router.get(
#     '/letterboxd-list/{list_slug}',
#     tags=['letterboxd-list'],
#     summary="Scrape and Fetch Letterboxd List"
#   )
# async def scrape_letterboxd_list(
#   list_slug: str,
#   parse_extra_pages: bool = True,
#   film_parse_limit: int = None,
#   db: AsyncMongoClient = Depends(get_database)
# ) -> ListHistory:
#   '''
#     Performs a webscraping function to extract data from lazy-loaded DOM
#     in Letterboxd.
#   '''

#   history_id = uuid.uuid4()
#   created_at = strip_tz(datetime.now(timezone.utc))
#   page = requests.get(lboxd_list_link)
#   soup = BeautifulSoup(page.content, 'lxml')
#   save_scrape = False

#   list_object = LetterboxdList(soup)
#   list_name = list_object.list_name
#   publish_date = list_object.publish_date
#   last_update = list_object.last_update
#   total_pages = list_object.total_pages
#   pages = getExtraPages(soup)
#   results = soup.find_all('li', 'poster-container', limit=film_parse_limit)

#   try:
#     await db.command('ping')
#   except Exception:
#     raise HTTPException(status_code=500, detail="Database connection error")

#   list_entry = await parse_list(lboxd_list_id, db)
#   list_entry_date = list_entry['last_update']
#   if list_entry_date == last_update:
#     return jsonable_encoder(list_entry)
#   else:
#     save_scrape = True

#   films = []
  
#   for result in results:
#     rank_placement = getRankPlacement(result)
#     film_poster = result.find('div', 'film-poster')
#     film_id = film_poster['data-film-id']
#     film_slug = film_poster['data-film-slug']

#     film = {
#       'rank': rank_placement,
#       'film_id': film_id,
#     }

#     query = { '_id': { '$eq': film_id } }
#     film_in_db = await query_db(db, query, 'movie')
#     # NOTE: explore adding additional flag to check if changes in movie were made
#     if not film_in_db:
#       print(f"New film detected in list! Parsing film_id: {film_id}")
#       result = scrape_movie(film_slug, film_id)
#       film_data = result['data']
#       film_numerical_stats = {
#         'rating': film_data['rating'] if 'rating' in film_data else None,
#         'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
#         'review_count': film_data['review_count'] if 'review_count' in film_data else None,
#         'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
#         'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
#         'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
#         'like_count': film_data['like_count'] if 'like_count' in film_data else None,
#       }

#       movie_history_id = uuid.uuid4()
#       movie_history_created_at = strip_tz(datetime.now(timezone.utc))
#       movie_history = {
#         **film_data,
#         '_id': Binary.from_uuid(movie_history_id),
#         'list_id': history_id,
#         'film_id': film_id,
#         'created_at': movie_history_created_at,
#       }
#       await update_db(db, movie_history, 'movie_history')
      
#       movie = strip_descriptive_stats(film_data)
#       await update_db(db, movie, 'movie')

#       film = {
#         **film,
#         **film_numerical_stats
#       }
#     else:

#       # TODO: include a flag in this API to add to movie_history since the list is new
#       movie_history_query = { 'film_id': { '$eq': film_id }}
#       latest_film = await query_db(db, movie_history_query, 'movie_history')
#       film_data = latest_film[0]

#       # if save_scrape:
#       #   result = scrape_movie(film_slug, film_id)
#       #   film_data = result['data']
#       #   film_numerical_stats = {
#       #     'rating': film_data['rating'] if 'rating' in film_data else None,
#       #     'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
#       #     'review_count': film_data['review_count'] if 'review_count' in film_data else None,
#       #     'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
#       #     'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
#       #     'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
#       #     'like_count': film_data['like_count'] if 'like_count' in film_data else None,
#       #   }

#       #   movie_history_id = uuid.uuid4()
#       #   movie_history_created_at = strip_tz(datetime.now(timezone.utc))
#       #   movie_history = {
#       #     **film_data,
#       #     '_id': Binary.from_uuid(movie_history_id),
#       #     'list_id': history_id,
#       #     'film_id': film_id,
#       #     'created_at': movie_history_created_at,
#       #   }
#       #   await update_db(db, movie_history, 'movie_history')

#       # if save_scrape == True: get

#       film_numerical_stats = {
#         'rating': film_data['rating'] if 'rating' in film_data else None,
#         'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
#         'review_count': film_data['review_count'] if 'review_count' in film_data else None,
#         'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
#         'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
#         'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
#         'like_count': film_data['like_count'] if 'like_count' in film_data else None,
#       }
#       film = {
#         **film,
#         **film_numerical_stats
#       }

#     films.append(film)

#   if pages and parse_extra_pages:
#     for page in pages:
#       html_page = requests.get(lboxd_url + page)
#       soup = BeautifulSoup(html_page.content, 'lxml')
#       results = soup.find_all('li', 'poster-container', limit=film_parse_limit)
#       for result in results:
#         rank_placement = getRankPlacement(result)
#         film_poster = result.find('div', 'film-poster')
#         film_id = film_poster['data-film-id']
#         film_slug = film_poster['data-film-slug']

#         film = {
#           'rank': rank_placement,
#           'film_id': film_id,
#         }

#         query = { '_id': { '$eq': film_id } }
#         film_in_db = await query_db(db, query, 'movie')
#         if not film_in_db:
#           print(f"New film detected in list! Parsing film_id: {film_id}")
#           result = scrape_movie(film_slug, film_id)
#           film_data = result['data']
#           film_numerical_stats = {
#             'rating': film_data['rating'] if 'rating' in film_data else None,
#             'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
#             'review_count': film_data['review_count'] if 'review_count' in film_data else None,
#             'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
#             'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
#             'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
#             'like_count': film_data['like_count'] if 'like_count' in film_data else None,
#           }

#           movie_history_id = uuid.uuid4()
#           movie_history_created_at = strip_tz(datetime.now(timezone.utc))
#           movie_history = {
#             **film_data,
#             '_id': Binary.from_uuid(movie_history_id),
#             'list_id': history_id,
#             'film_id': film_id,
#             'created_at': movie_history_created_at,
#           }
#           await update_db(db, movie_history, 'movie_history')

#           movie = strip_descriptive_stats(film_data)
#           await update_db(db, movie, 'movie')
          
#           film = {
#             **film,
#             **film_numerical_stats
#           }
#         else:
#           movie_history_query = { 'film_id': { '$eq': film_id }}
#           latest_film = await query_db(db, movie_history_query, 'movie_history')
#           film_data = latest_film[0]
#           film_numerical_stats = {
#             'rating': film_data['rating'] if 'rating' in film_data else None,
#             'classic_rating': film_data['classic_rating'] if 'classic_rating' in film_data else None,
#             'review_count': film_data['review_count'] if 'review_count' in film_data else None,
#             'rating_count': film_data['rating_count'] if 'rating_count' in film_data else None,
#             'watch_count': film_data['watch_count'] if 'watch_count' in film_data else None,
#             'list_appearance_count': film_data['list_appearance_count'] if 'list_appearance_count' in film_data else None,
#             'like_count': film_data['like_count'] if 'like_count' in film_data else None,
#           }
#           film = {
#             **film,
#             **film_numerical_stats
#           }
        
#         films.append(film)
  
#   list_history = {
#     "_id": history_id,
#     "list_id": lboxd_list_id,
#     "list_name": list_name,
#     "total_pages": total_pages,
#     "data": films, 
#     "publish_date": publish_date,
#     "last_update": last_update,
#     "created_at": created_at
#   }

#   if save_scrape:
#     save_list = {
#       "_id": Binary.from_uuid(history_id),
#       "list_id": lboxd_list_id,
#       "list_name": list_name,
#       "total_pages": total_pages,
#       "data": films,
#       "publish_date": publish_date,
#       "last_update": last_update,
#       "created_at": created_at
#     }
#     await update_db(db, save_list, 'list_history')

#   return list_history

# @router.get(
#     '/movie/scrape/{film_slug}', 
#     tags=['movie'], 
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