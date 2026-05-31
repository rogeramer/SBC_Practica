import re
from difflib import SequenceMatcher


class SteamLibraryManager:
    def __init__(self, steam_service, rawg_service):
        self.steam = steam_service
        self.rawg = rawg_service

    def load_library(self, steamid: str):
        return self.steam.get_owned_games(steamid)

    def normalize_name(self, name):
        name = (name or "").lower()
        name = name.replace("®", "").replace("™", "")
        name = name.replace(":", " ").replace("-", " ")
        name = re.sub(r"\([^)]*\)", " ", name)
        name = re.sub(r"[^a-z0-9\s]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def build_library_map(self, steam_games):
        library_map = {}

        for game in steam_games:
            normalized_name = self.normalize_name(game.get("name"))

            if normalized_name:
                library_map[normalized_name] = game

        return library_map

    def _find_matching_steam_game(self, rawg_name, steam_library_map):
        normalized_rawg_name = self.normalize_name(rawg_name)

        # Coincidencia exacta tras normalización
        if normalized_rawg_name in steam_library_map:
            return steam_library_map[normalized_rawg_name]

        best_match = None
        best_score = 0

        for steam_name, steam_game in steam_library_map.items():

            # Evitar falsos positivos por secuelas o números romanos
            if not self._numbers_are_compatible(
                    normalized_rawg_name,
                    steam_name
            ):
                continue

            score = SequenceMatcher(
                None,
                normalized_rawg_name,
                steam_name
            ).ratio()

            if score > best_score:
                best_score = score
                best_match = steam_game

        if best_score >= 0.88:
            return best_match

        return None
    
    def _extract_numbers(self, name):
        """
        Extrae números normales y romanos relevantes del nombre.
        """
        roman_numerals = {
            "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"
        }

        tokens = set(self.normalize_name(name).split())

        numeric_tokens = {
            token for token in tokens
            if token.isdigit() or token in roman_numerals
        }

        return numeric_tokens

    def _numbers_are_compatible(self, rawg_name, steam_name):
        """
        Evita asociar juegos distintos de una misma saga:
        Elder Scrolls V != Elder Scrolls VI
        Fallout 3 != Fallout 4
        """
        rawg_numbers = self._extract_numbers(rawg_name)
        steam_numbers = self._extract_numbers(steam_name)

        if rawg_numbers and steam_numbers:
            return rawg_numbers == steam_numbers

        return True

    def filter_owned_games_from_rawg_results(self, rawg_games, steam_library_map):
        if not steam_library_map:
            return []

        owned_results = []

        for game in rawg_games:
            steam_game = self._find_matching_steam_game(
                game.get("name", ""),
                steam_library_map
            )

            if steam_game:
                merged = dict(game)
                merged["steam_playtime_forever"] = steam_game.get("playtime_forever", 0)
                merged["steam_appid"] = steam_game.get("appid")
                merged["steam_rtime_last_played"] = steam_game.get("rtime_last_played", 0)
                owned_results.append(merged)

        return owned_results

    def recommend_from_library(self, rawg_result, steam_library_map, limit=5, prioritize_less_played=True):
        rawg_games = rawg_result.get("results", [])
        owned_games = self.filter_owned_games_from_rawg_results(rawg_games, steam_library_map)

        if prioritize_less_played:
            owned_games.sort(key=lambda g: g.get("steam_playtime_forever", 0))

        return owned_games[:limit]

    def format_library_recommendations(self, games):
        if not games:
            return (
                "No he encontrado coincidencias dentro de tu biblioteca de Steam con esos criterios.\n\n"
                "Puede que RAWG y Steam usen nombres distintos para algunos juegos, o que los filtros sean demasiado concretos.\n\n"
                "Prueba con algo más general como:\n"
                "• algo de mi biblioteca\n"
                "• un juego de accion de mi biblioteca\n"
                "• un juego relajado de mi biblioteca"
            )

        lines = ["He encontrado estos juegos dentro de tu biblioteca de Steam:\n"]

        for i, game in enumerate(games, start=1):
            playtime = game.get("steam_playtime_forever", 0)
            hours = round(playtime / 60, 1)
            genres = ", ".join(g["name"] for g in game.get("genres", [])[:3]) or "Sin género"

            lines.append(
                f"{i}. 🎮 {game.get('name', 'Sin nombre')}\n"
                f"   • Horas jugadas en Steam: {hours}\n"
                f"   • Rating RAWG: {game.get('rating', 'N/A')}\n"
                f"   • Metacritic: {game.get('metacritic', 'N/A')}\n"
                f"   • Géneros: {genres}\n"
            )

        lines.append(
            "\nPuedes decirme:\n"
            "• detalles del 1\n"
            "• otro juego de mi biblioteca\n"
            "• un juego de accion de mi biblioteca"
        )

        return "\n".join(lines)

    def format_library_loaded_message(self, steamid, game_count):
        return (
            f"Biblioteca de Steam cargada correctamente.\n"
            f"SteamID: {steamid}\n"
            f"Juegos visibles: {game_count}\n\n"
            f"Ahora puedes pedirme cosas como:\n"
            f"• recomiendame algo de mi biblioteca\n"
            f"• un rpg de mi biblioteca\n"
            f"• un juego con historia de mi biblioteca"
        )

    def get_most_played_game(self, steam_games):

        if not steam_games:
            return None

        return max(
            steam_games,
            key=lambda g: g.get("playtime_forever", 0)
        )