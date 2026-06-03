import re
import unicodedata
from difflib import SequenceMatcher

class SteamLibraryManager:
    MATCH_THRESHOLD = 0.88
    MIN_TOKEN_OVERLAP = 0.60

    def __init__(self, steam_service, rawg_service):
        self.steam = steam_service
        self.rawg = rawg_service

    def load_library(self, steamid):
        return self.steam.get_owned_games(
            steamid
        )

    def normalize_name(self, name):
        name = str(name or "").lower()
        name = unicodedata.normalize(
            "NFKD",
            name,
        )
        name = name.encode(
            "ascii",
            "ignore",
        ).decode(
            "ascii"
        )
        name = name.replace(
            "®",
            ""
        ).replace(
            "™",
            ""
        )
        name = re.sub(
            r"\([^)]*\)",
            " ",
            name,
        )
        name = re.sub(
            r"[^a-z0-9\s]",
            " ",
            name,
        )
        return re.sub(
            r"\s+",
            " ",
            name,
        ).strip()

    def build_library_map(self, steam_games):
        library_map = {}
        for game in steam_games:
            normalized_name = self.normalize_name(
                game.get("name")
            )
            if normalized_name:
                library_map[
                    normalized_name
                ] = game
        return library_map

    def _extract_numbers(self, name):
        roman_numerals = {
            "i",
            "ii",
            "iii",
            "iv",
            "v",
            "vi",
            "vii",
            "viii",
            "ix",
            "x",
        }
        tokens = set(
            self.normalize_name(name).split()
        )
        return {
            token
            for token in tokens
            if (
                token.isdigit()
                or token in roman_numerals
            )
        }

    def _numbers_are_compatible(
        self,
        rawg_name,
        steam_name,
    ):
        rawg_numbers = self._extract_numbers(
            rawg_name
        )
        steam_numbers = self._extract_numbers(
            steam_name
        )
        return rawg_numbers == steam_numbers

    def _calculate_token_overlap(
        self,
        first_name,
        second_name,
    ):
        first_tokens = set(
            self.normalize_name(
                first_name
            ).split()
        )
        second_tokens = set(
            self.normalize_name(
                second_name
            ).split()
        )
        if not first_tokens or not second_tokens:
            return 0.0
        shared_tokens = (
            first_tokens.intersection(
                second_tokens
            )
        )
        smallest_size = min(
            len(first_tokens),
            len(second_tokens),
        )
        return len(shared_tokens) / smallest_size

    def _find_matching_steam_game(
        self,
        rawg_name,
        steam_library_map,
    ):
        normalized_rawg_name = (
            self.normalize_name(
                rawg_name
            )
        )
        if not normalized_rawg_name:
            return None
        if (
            normalized_rawg_name
            in steam_library_map
        ):
            return steam_library_map[
                normalized_rawg_name
            ]
        best_match = None
        best_score = 0.0
        for (
            steam_name,
            steam_game,
        ) in steam_library_map.items():
            if not self._numbers_are_compatible(
                normalized_rawg_name,
                steam_name,
            ):
                continue
            token_overlap = (
                self._calculate_token_overlap(
                    normalized_rawg_name,
                    steam_name,
                )
            )
            if (
                token_overlap
                < self.MIN_TOKEN_OVERLAP
            ):
                continue
            score = SequenceMatcher(
                None,
                normalized_rawg_name,
                steam_name,
            ).ratio()
            if score > best_score:
                best_score = score
                best_match = steam_game
        if best_score >= self.MATCH_THRESHOLD:
            return best_match
        return None

    def filter_owned_games_from_rawg_results(
        self,
        rawg_games,
        steam_library_map,
    ):
        if not steam_library_map:
            return []
        owned_results = []
        used_appids = set()

        for game in rawg_games:
            steam_game = (
                self._find_matching_steam_game(
                    game.get("name", ""),
                    steam_library_map,
                )
            )
            if not steam_game:
                continue
            appid = steam_game.get("appid")
            if (
                appid is not None
                and appid in used_appids
            ):
                continue
            if appid is not None:
                used_appids.add(appid)
            merged = dict(game)
            merged[
                "steam_playtime_forever"
            ] = steam_game.get(
                "playtime_forever",
                0,
            )
            merged[
                "steam_appid"
            ] = appid

            merged[
                "steam_rtime_last_played"
            ] = steam_game.get(
                "rtime_last_played",
                0,
            )
            owned_results.append(
                merged
            )
        return owned_results

    def recommend_from_library(
        self,
        rawg_result,
        steam_library_map,
        limit=5,
        prioritize_less_played=True,
    ):
        rawg_games = rawg_result.get(
            "results",
            []
        )
        owned_games = (
            self.filter_owned_games_from_rawg_results(
                rawg_games,
                steam_library_map,
            )
        )
        if prioritize_less_played:
            owned_games.sort(
                key=lambda game: game.get(
                    "steam_playtime_forever",
                    0,
                )
            )
        return owned_games[:limit]

    def _format_reasons_text(self, reasons):
        cleaned_reasons = []
        for reason in reasons:
            reason = str(reason).strip()
            if not reason:
                continue
            cleaned_reasons.append(
                reason[0].upper()
                + reason[1:]
            )
        if not cleaned_reasons:
            return ""
        return ". ".join(
            cleaned_reasons
        ) + "."

    def format_library_recommendations(
        self,
        games,
    ):
        if not games:
            return (
                "No he encontrado coincidencias dentro de tu "
                "biblioteca de Steam con esos criterios.\n\n"
                "Puede que RAWG y Steam usen nombres distintos "
                "para algunos juegos, o que los filtros sean "
                "demasiado concretos.\n\n"
                "Prueba con algo más general como:\n"
                "• algo de mi biblioteca\n"
                "• un juego de acción de mi biblioteca\n"
                "• un juego relajado de mi biblioteca"
            )

        lines = [
            "He encontrado estos juegos dentro "
            "de tu biblioteca de Steam:\n"
        ]
        for index, game in enumerate(
            games,
            start=1,
        ):
            playtime = game.get(
                "steam_playtime_forever",
                0,
            )
            hours = round(
                playtime / 60,
                1,
            )
            genres = ", ".join(
                genre["name"]
                for genre in game.get(
                    "genres",
                    [],
                )[:3]
            ) or "Sin género"
            reasons = game.get(
                "_recommendation_reasons",
                [],
            )
            reasons_text = ""
            if reasons:
                reasons_text = (
                    "   • Por qué encaja: "
                    f"{self._format_reasons_text(reasons)}\n"
                )
            lines.append(
                f"{index}. 🎮 {game.get('name', 'Sin nombre')}\n"
                f"   • Horas jugadas en Steam: {hours}\n"
                f"   • Rating RAWG: {game.get('rating') or 'No disponible'}\n"
                f"   • Metacritic: {game.get('metacritic') or 'No disponible'}\n"
                f"   • Géneros: {genres}\n"
                f"{reasons_text}"
            )

        lines.append(
            "\nPuedes decirme:\n"
            "• detalles del 1\n"
            "• otro juego de mi biblioteca\n"
            "• un juego de acción de mi biblioteca"
        )
        return "\n".join(lines)

    def format_library_loaded_message(
        self,
        steamid,
        game_count,
    ):
        return (
            "Biblioteca de Steam cargada correctamente.\n"
            f"SteamID: {steamid}\n"
            f"Juegos visibles: {game_count}\n\n"
            "Ahora puedes pedirme cosas como:\n"
            "• recomiéndame algo de mi biblioteca\n"
            "• un RPG de mi biblioteca\n"
            "• un juego con historia de mi biblioteca"
        )

    def get_most_played_game(
        self,
        steam_games,
    ):
        if not steam_games:
            return None
        return max(
            steam_games,
            key=lambda game: game.get(
                "playtime_forever",
                0,
            ),
        )