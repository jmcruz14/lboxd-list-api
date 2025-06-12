from dependencies import DatabaseDep
from fastapi.exceptions import HTTPException
from fastapi import APIRouter
from services import ListService

list_route = APIRouter()
@list_route.get('/list-history', tags=['letterboxd-list'], summary="Fetch stored list-history item")
async def fetch_list_history(id: int, db: DatabaseDep, fetch_movies: bool = False):
  list_service = ListService(db)
  try:
    result = await list_service.get_latest_list_by_id(str(id), fetch_movies)
    if not result:
        raise HTTPException(status_code=404, detail="List history not found")
    return result
  except HTTPException:
    raise
  except Exception as e:
    if "Database connection error" in str(e):
        raise HTTPException(status_code=500, detail="Database connection error")
    raise HTTPException(status_code=500, detail=f"Failed to fetch list history: {str(e)}")
