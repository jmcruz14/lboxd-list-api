import logging
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers.dbconnect import connect_server
from routers.list import list_route
from routers.movie import movie_route
# from routers.scraper import scraper_route

# Saved app variable will be run in the shell script
app = FastAPI(
  title="LetterboxdListDashboardAPI",
  version="0.3.2",
  lifespan=connect_server
)
origins = [
  # "https://localhost:3000",
  # "http://localhost:3000",
  # "https://top-250-website.vercel.app/"
  "*"
]
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

lboxd_url = 'https://letterboxd.com'
lboxd_list_id = '15294077'

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
  print(f"{repr(exc)}")
  return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

app.include_router(list_route)
app.include_router(movie_route)
# app.include_router(scraper_route)

@app.get('/', include_in_schema=True)
async def root(request: Request, status_code=301):
  redirect_url = request.url_for(
    'fetch_movie_history',
    id=15294077
  )
  return RedirectResponse(redirect_url)