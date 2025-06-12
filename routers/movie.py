from fastapi.exceptions import HTTPException
from fastapi import APIRouter
from dependencies import DatabaseDep
from models import MovieOut, MovieHistoryOut
# from routers.dbconnect import query_db
from services import MovieService

movie_route = APIRouter()

@movie_route.get(
  '/movie/fetch/{id}', 
  tags=['movie'], 
  summary="Fetch movie in db", 
  response_model=None
  # response_model_exclude_none=True
)
async def fetch_movie(
  id,
  db: DatabaseDep
):
  movie_service = MovieService(db)

  try:
    movie_data = await movie_service.get_movie_by_id(str(id))
    
    if not movie_data:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    return MovieOut(data=movie_data)
      
  except HTTPException:
      raise
  except Exception as e:
      if "Database connection error" in str(e):
          raise HTTPException(status_code=500, detail="Database connection error")
      raise HTTPException(status_code=500, detail=f"Failed to fetch movie: {str(e)}")


@movie_route.get('/movie_history/fetch/{id}', tags=['movie'], summary="Fetch movie_history in db")
async def fetch_movie_history(
  id: int | str, 
  db: DatabaseDep
) -> MovieHistoryOut:
  """
    Fetches movie history data for a film.

    Args:
      id (int)
      db (DatabaseDep)
  """
  movie_service = MovieService(db)
    
  try:
      movie_history = await movie_service.get_movie_history_by_film_id(str(id))
      if not movie_history:
          raise HTTPException(status_code=404, detail="Movie history not found")
          
      return MovieHistoryOut(data=movie_history)
      
  except HTTPException:
      raise
  except Exception as e:
      if "Database connection error" in str(e):
          raise HTTPException(status_code=500, detail="Database connection error")
      raise HTTPException(status_code=500, detail=f"Failed to fetch movie history: {str(e)}")

