import os
import requests
from dotenv import load_dotenv

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY", "").strip()
BASE_URL = "https://partner.steam-api.com"

if not STEAM_API_KEY:
    raise ValueError("Falta STEAM_API_KEY en el archivo .env")


class SteamService:
    def __init__(self):
        self.session = requests.Session()

    def _get(self, endpoint, params=None):
        params = params or {}
        params["key"] = STEAM_API_KEY

        response = self.session.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    def is_valid_steamid64(self, steamid: str) -> bool:
        return steamid.isdigit() and len(steamid) == 17

    def get_owned_games(self, steamid: str, include_played_free_games: bool = True):
        """
        Devuelve:
        {
            "status": "ok" | "not_accessible" | "invalid_id",
            "games": [...],
            "game_count": int,
            "message": str
        }
        """
        if not self.is_valid_steamid64(steamid):
            return {
                "status": "invalid_id",
                "games": [],
                "game_count": 0,
                "message": "El SteamID debe ser un SteamID64 válido de 17 dígitos."
            }

        data = self._get(
            "/IPlayerService/GetOwnedGames/v1/",
            {
                "steamid": steamid,
                "include_appinfo": "true",
                "include_played_free_games": "true" if include_played_free_games else "false",
            }
        )

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
                    "a que la biblioteca o los detalles de juegos no sean públicos, "
                    "o a que no haya juegos visibles."
                )
            }

        normalized_games = []
        for game in games:
            normalized_games.append({
                "appid": game.get("appid"),
                "name": game.get("name", "Unknown"),
                "img_icon_url": game.get("img_icon_url", ""),
                "playtime_forever": game.get("playtime_forever", 0),
                "playtime_windows_forever": game.get("playtime_windows_forever", 0),
                "playtime_mac_forever": game.get("playtime_mac_forever", 0),
                "playtime_linux_forever": game.get("playtime_linux_forever", 0),
                "rtime_last_played": game.get("rtime_last_played", 0),
            })

        return {
            "status": "ok",
            "games": normalized_games,
            "game_count": game_count,
            "message": f"Biblioteca cargada correctamente ({game_count} juegos visibles)."
        }