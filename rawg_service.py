import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.rawg.io/api"
DEFAULT_TIMEOUT = 15

class RawgService:
    def __init__(self, api_key=None, timeout=DEFAULT_TIMEOUT):
        self.api_key = (
            api_key
            or os.getenv("RAWG_API_KEY", "").strip()
        )

        if not self.api_key:
            raise ValueError(
                "Falta RAWG_API_KEY en el archivo .env"
            )

        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SBC-GameBot/1.0",
        })

    def _get(self, endpoint, params=None):
        request_params = dict(params or {})
        request_params["key"] = self.api_key

        try:
            response = self.session.get(
                f"{BASE_URL}{endpoint}",
                params=request_params,
                timeout=self.timeout,
            )

        except requests.Timeout as error:
            raise RuntimeError(
                "RAWG ha tardado demasiado en responder."
            ) from error

        except requests.ConnectionError as error:
            raise RuntimeError(
                "No se ha podido conectar con RAWG. "
                "Comprueba tu conexión a Internet."
            ) from error

        except requests.RequestException as error:
            raise RuntimeError(
                "Ha ocurrido un error al realizar la petición a RAWG."
            ) from error

        if not response.ok:
            raise RuntimeError(
                "RAWG ha devuelto un error "
                f"HTTP {response.status_code}."
            )

        try:
            return response.json()

        except ValueError as error:
            raise RuntimeError(
                "RAWG ha devuelto una respuesta no válida."
            ) from error

    def _get_results(self, endpoint, params=None):
        data = self._get(endpoint, params)
        return data.get("results", [])

    def get_genres(self, page_size=40):
        return self._get_results(
            "/genres",
            {
                "page_size": page_size,
            },
        )

    def get_tags(self, page_size=40):
        return self._get_results(
            "/tags",
            {
                "page_size": page_size,
            },
        )

    def get_platforms(self, page_size=50):
        return self._get_results(
            "/platforms",
            {
                "page_size": page_size,
            },
        )

    def get_stores(self, page_size=30):
        return self._get_results(
            "/stores",
            {
                "page_size": page_size,
            },
        )

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

        return self._get(
            "/games",
            params,
        )

    def get_game_details(self, slug):
        safe_slug = quote(
            str(slug),
            safe="",
        )

        return self._get(
            f"/games/{safe_slug}"
        )

    def get_game_screenshots(self, game_id):
        return self._get_results(
            f"/games/{game_id}/screenshots"
        )

    def get_game_trailers(self, game_id):
        return self._get_results(
            f"/games/{game_id}/movies"
        )

    def close(self):
        self.session.close()