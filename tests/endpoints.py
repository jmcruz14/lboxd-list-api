# import os
# import json
# import certifi
# import urllib.parse as parse
# from contextlib import asynccontextmanager
# from pymongo import AsyncMongoClient
# from main import app
# from fastapi.testclient import TestClient
import logging
logger = logging.getLogger(__name__)

class TestRootEndpoint:
  def test_root_redirect(self, client):
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 307
    logger.info(response.headers)
    assert "movie_history/fetch/15294077" in response.headers["location"]