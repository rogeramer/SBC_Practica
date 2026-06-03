import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.steampowered.com"
DEFAULT_TIMEOUT = 15


class SteamService:
    def __init__(self, api_key=None, timeout=DEFAULT_TIMEOUT):
        self.api_key = (
            api_key
            or os.getenv("STEAM_API_KEY", "").strip()
        )
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SBC-GameBot/1.0",
        })

    def _get(self, endpoint, params=None):

        if not self.api_key:
            raise RuntimeError(
                "Falta STEAM_API_KEY en el archivo .env. "
                "Configúrala para utilizar las funciones de Steam."
            )

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
                "Steam ha tardado demasiado en responder."
            ) from error

        except requests.ConnectionError as error:
            raise RuntimeError(
                "No se ha podido conectar con Steam. "
                "Comprueba tu conexión a Internet."
            ) from error

        except requests.RequestException as error:
            raise RuntimeError(
                "Ha ocurrido un error al realizar la petición a Steam."
            ) from error

        if not response.ok:
            raise RuntimeError(
                "Steam ha devuelto un error "
                f"HTTP {response.status_code}."
            )

        try:
            return response.json()

        except ValueError as error:
            raise RuntimeError(
                "Steam ha devuelto una respuesta no válida."
            ) from error

    def is_valid_steamid64(self, steamid):
        return (
            isinstance(steamid, str)
            and steamid.isdigit()
            and len(steamid) == 17
        )

    def get_owned_games(
        self,
        steamid,
        include_played_free_games=True,
    ):
        if not self.api_key:
            return {
                "status": "missing_key",
                "games": [],
                "game_count": 0,
                "message": (
                    "La integración con Steam no está configurada. "
                    "Falta STEAM_API_KEY en el archivo .env."
                ),
            }

        if not self.is_valid_steamid64(steamid):
            return {
                "status": "invalid_id",
                "games": [],
                "game_count": 0,
                "message": (
                    "El SteamID debe ser un SteamID64 válido "
                    "de 17 dígitos."
                ),
            }

        try:
            data = self._get(
                "/IPlayerService/GetOwnedGames/v1/",
                {
                    "steamid": steamid,
                    "include_appinfo": "true",
                    "include_played_free_games": (
                        "true"
                        if include_played_free_games
                        else "false"
                    ),
                    "format": "json",
                },
            )

        except RuntimeError as error:
            return {
                "status": "service_error",
                "games": [],
                "game_count": 0,
                "message": str(error),
            }
        response = data.get("response", {})
        games = response.get("games", [])
        game_count = response.get("game_count", 0)
        if not games:
            return {
                "status": "not_accessible",
                "games": [],
                "game_count": 0,
                "message": (
                    "No he podido recuperar juegos de esta cuenta. "
                    "Puede deberse a que el SteamID no sea correcto, "
                    "a que la biblioteca o los detalles de juegos "
                    "no sean públicos, o a que no haya juegos visibles."
                ),
            }
        normalized_games = [
            self._normalize_game(game)
            for game in games
        ]
        return {
            "status": "ok",
            "games": normalized_games,
            "game_count": game_count,
            "message": (
                "Biblioteca cargada correctamente "
                f"({game_count} juegos visibles)."
            ),
        }

    def _normalize_game(self, game):
        return {
            "appid": game.get("appid"),
            "name": game.get("name", "Unknown"),
            "img_icon_url": game.get("img_icon_url", ""),
            "playtime_forever": game.get(
                "playtime_forever",
                0,
            ),
            "playtime_windows_forever": game.get(
                "playtime_windows_forever",
                0,
            ),
            "playtime_mac_forever": game.get(
                "playtime_mac_forever",
                0,
            ),
            "playtime_linux_forever": game.get(
                "playtime_linux_forever",
                0,
            ),
            "rtime_last_played": game.get(
                "rtime_last_played",
                0,
            ),
        }

    def close(self):
        self.session.close()
