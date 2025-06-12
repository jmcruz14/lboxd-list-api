'''Conftest.py is a file used by the pytest module to 
create 'dependency injection' type values enclosed within
a fixture function.

The name of the function in each fixture must share a name with a parameter
in any test script.
'''

import certifi
import pytest
import pymongo
import os
from fastapi.testclient import TestClient
from main import app
from urllib.parse import quote_plus

@pytest.fixture(scope="session")
def client():
  return TestClient(app)

@pytest.fixture(scope="session")
def mongodb():
  MONGODB_UNAME = quote_plus(os.environ["MONGODB_USERNAME"])
  MONGODB_PW = quote_plus(os.environ["MONGODB_PASSWORD"])
  MONGODB_HOST = os.environ["MONGODB_HOST"]
  uri = f"mongodb+srv://{MONGODB_UNAME}:{MONGODB_PW}@{MONGODB_HOST}"
  client = pymongo.MongoClient(
      uri,
      tlsCAFile=certifi.where(),
      uuidRepresentation='standard'
    )
  assert client.admin.command("ping")["ok"] != 0.0 # Check that the connection is okay.
  return client

@pytest.fixture(scope="session")
def rollback_session(mongodb):
  session = mongodb.start_session()
  session.start_transaction()
  try:
    yield session
  finally:
    session.abort_transaction()