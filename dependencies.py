from fastapi import Depends
from typing import Annotated
from pymongo import AsyncMongoClient

# This will be set by main.py during app startup
_app_database = None

def set_database(database: AsyncMongoClient):
  """Set the database instance from main.py"""
  global _app_database
  _app_database = database

async def get_database() -> AsyncMongoClient:
  """Dependency function to get database connection"""
  if _app_database is None:
      raise RuntimeError("Database not initialized")
  return _app_database

DatabaseDep = Annotated[AsyncMongoClient, Depends(get_database)]

__all__ = (set_database, get_database,)