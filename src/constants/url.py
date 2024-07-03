DOMAIN = "https://letterboxd.com/"

def fetchMovieWatchersUrl(slug: str) -> str:
  return f"https://letterboxd.com/film/{slug}/members/"

def fetchStatsUrl(slug: str) -> str:
  return f"https://letterboxd.com/csi/film/{slug}/stats/"

def fetchRatingHistogramUrl(slug: str) -> str:
  return f"https://letterboxd.com/csi/film/{slug}/rating-histogram/"