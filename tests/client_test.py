'''This test script is dedicated specifically to checking if the endpoints are still working as intended'''
import os
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_scrape_movie():
    film_slug = os.environ["MOVIE_SLUG"]
    response = client.get(f"/movie/scrape/{film_slug}")
    assert response.status_code == 200

    data = response.json()['data']
    assert data['film_slug'] == 'norte-the-end-of-history'
    assert data['film_title'] == 'Norte, The End of History'
    assert data['year'] == 2013
    assert data['genre'] == ['Drama', 'Crime']
    assert data['runtime'] == 250