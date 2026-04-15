import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAWG_API_KEY = os.getenv("RAWG_API_KEY", "").strip()
BASE_URL = "https://api.rawg.io/api"

if not RAWG_API_KEY:
    raise ValueError("Falta RAWG_API_KEY en el archivo .env")


class RawgService:
    def __init__(self):
        self.session = requests.Session()

    def _get(self, endpoint, params=None):
        params = params or {}
        params["key"] = RAWG_API_KEY

        response = self.session.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    def get_genres(self, page_size=40):
        data = self._get("/genres", {"page_size": page_size})
        return data.get("results", [])

    def get_tags(self, page_size=40):
        data = self._get("/tags", {"page_size": page_size})
        return data.get("results", [])

    def get_platforms(self, page_size=50):
        data = self._get("/platforms", {"page_size": page_size})
        return data.get("results", [])

    def get_stores(self, page_size=30):
        data = self._get("/stores", {"page_size": page_size})
        return data.get("results", [])

    def search_games(
        self,
        search=None,
        genres=None,
        tags=None,
        platforms=None,
        ordering="-rating",
        dates=None,
        metacritic=None,
        page=1,
        page_size=8,
        search_exact=False,
        search_precise=False,
    ):
        params = {
            "page": page,
            "page_size": page_size,
            "ordering": ordering,
        }

        if search:
            params["search"] = search
        if genres:
            params["genres"] = genres
        if tags:
            params["tags"] = tags
        if platforms:
            params["platforms"] = platforms
        if dates:
            params["dates"] = dates
        if metacritic:
            params["metacritic"] = metacritic
        if search_exact:
            params["search_exact"] = "true"
        if search_precise:
            params["search_precise"] = "true"

        return self._get("/games", params)

    def get_game_details(self, slug):
        return self._get(f"/games/{slug}")

    def get_game_screenshots(self, game_id):
        data = self._get(f"/games/{game_id}/screenshots")
        return data.get("results", [])

    def get_game_trailers(self, game_id):
        data = self._get(f"/games/{game_id}/movies")
        return data.get("results", [])