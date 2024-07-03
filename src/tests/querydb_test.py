import os
import json
import certifi
import urllib.parse as parse
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from main import app, get_database
from fastapi.testclient import TestClient
from models.query import MovieStatsQuery, StatQuery
client = TestClient(app)
MONGODB_UNAME = parse.quote_plus(os.environ['MONGODB_USERNAME'])
MONGODB_PW = parse.quote_plus(os.environ['MONGODB_PASSWORD'])
MONGODB_HOST = os.environ['MONGODB_HOST']
LBOXD_COLLECTION = os.environ['LBOXD_COLLECTION']

@asynccontextmanager
async def override_get_database():
  try:
    uri = f"mongodb+srv://{MONGODB_UNAME}:{MONGODB_PW}@{MONGODB_HOST}"
    app.mongodb_client = AsyncIOMotorClient(
      uri, 
      tlsCAFile=certifi.where(),
      uuidRepresentation='standard'
    )
    app.database = app.mongodb_client.get_default_database(LBOXD_COLLECTION)
    yield
  finally:
    app.mongodb_client.close()

app.dependency_overrides[get_database] = override_get_database

def test_mongodb_fixture(mongodb):
  """ This test will pass if MDB_URI is set to a valid connection string. """
  assert mongodb.admin.command("ping")["ok"] > 0

def test_query_db_list_history(mongodb, rollback_session):
  documents = mongodb.letterboxd_list.list_history.find({}, session=rollback_session)
  obj = [doc for doc in documents]

  assert documents is not None
  assert len(obj) >= 1

def test_query_db_movie(mongodb, rollback_session):
  query = {
    "director": "Lav Diaz"
  }
  documents = mongodb.letterboxd_list.movie.find(query, session=rollback_session)
  obj = [doc for doc in documents]

  assert documents is not None
  assert obj[0]['director'][0] == 'Lav Diaz'
  assert len(obj) >= 1

def test_query_db_pipeline(mongodb, rollback_session):
  pipeline = [
    {"$unwind": "$cast"},
    {"$match": {"cast": {"$ne": "Show All…"}}},
    {"$group": {
        "_id": "$cast",
        "count": {"$sum": 1}
    }},
    {"$match": {"count": {"$gte": 3, "$ne": "Show All…"}}},
    {"$sort": {"count": -1}}
  ]
  documents = mongodb.letterboxd_list.movie.aggregate(
    pipeline,
    session=rollback_session
  )
  obj = [doc for doc in documents]

  assert documents is not None
  assert len(obj) >= 1
  assert obj[0]['_id'] == 'Christopher de Leon'

def test_endpoint_pipeline(mongodb, rollback_session):
  stat = MovieStatsQuery(query=[
    StatQuery(field="cast", eq="Christopher de Leon"),
    StatQuery(field="director", eq="Lino Brocka")
  ])
  response = client.post('/movie-stats', json=stat.model_dump())
  print(response)

  assert response.status_code == 200