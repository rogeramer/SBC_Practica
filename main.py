import re

from rawg_service import RawgService
from steam_service import SteamService
from steam_library import SteamLibraryManager

from chatbot.intent_parser import detect_intent
from chatbot.filtres import FilterExtractor
from chatbot.formatter import (
    format_welcome_message,
    format_help_message,
    format_game_list,
    format_game_details,
    format_genres_list,
    format_platforms_list,
    format_reset_message,
    format_goodbye_message,
    format_no_results_message,
    format_error_message,
)


class RawgGameChatbot:
    def __init__(self):
        self.rawg = RawgService()
        self.steam = SteamService()
        self.steam_library_manager = SteamLibraryManager(self.steam, self.rawg)
        self.extractor = FilterExtractor(self.rawg)
        self.reset()

    def reset(self):
        self.context = {
            "search": None,
            "genres": [],
            "tags": [],
            "platforms": [],
            "ordering": "-rating",
            "dates": None,
            "metacritic": None,
            "last_results": [],
            "last_game_slug": None,
            "steam_id": None,
            "steam_library_loaded": False,
            "steam_library": [],
            "steam_library_map": {},
        }

    def _update_context(self, filters):
        if filters.get("search"):
            self.context["search"] = filters["search"]

        if filters.get("genres"):
            self.context["genres"] = filters["genres"]

        if filters.get("tags"):
            self.context["tags"] = filters["tags"]

        if filters.get("platforms"):
            self.context["platforms"] = filters["platforms"]

        if filters.get("ordering"):
            self.context["ordering"] = filters["ordering"]

        if filters.get("dates"):
            self.context["dates"] = filters["dates"]

        if filters.get("metacritic"):
            self.context["metacritic"] = filters["metacritic"]

    def _search_games_rawg(self, page_size=10):
        return self.rawg.search_games(
            search=self.context["search"],
            genres=",".join(self.context["genres"]) if self.context["genres"] else None,
            tags=",".join(self.context["tags"]) if self.context["tags"] else None,
            platforms=",".join(str(p) for p in self.context["platforms"]) if self.context["platforms"] else None,
            ordering=self.context["ordering"],
            dates=self.context["dates"],
            metacritic=self.context["metacritic"],
            page_size=page_size,
        )

    def _extract_steamid(self, text):
        match = re.search(r"\b\d{17}\b", text)
        return match.group(0) if match else None

    def _load_steam_library(self, steamid):
        library_result = self.steam_library_manager.load_library(steamid)

        if library_result["status"] != "ok":
            self.context["steam_id"] = steamid
            self.context["steam_library_loaded"] = False
            self.context["steam_library"] = []
            self.context["steam_library_map"] = {}
            return library_result["message"]

        games = library_result["games"]
        self.context["steam_id"] = steamid
        self.context["steam_library_loaded"] = True
        self.context["steam_library"] = games
        self.context["steam_library_map"] = self.steam_library_manager.build_library_map(games)

        return self.steam_library_manager.format_library_loaded_message(
            steamid,
            library_result["game_count"]
        )

    def _is_library_query(self, text):
        library_markers = [
            "mi biblioteca",
            "de mi biblioteca",
            "de steam",
            "mis juegos",
            "mis juegos comprados",
            "que ya tengo",
            "que ya poseo",
            "recomiendame algo que ya tengo",
            "recomiéndame algo que ya tengo",
        ]
        return any(marker in text for marker in library_markers)

    def _recommend_from_steam_library(self, clean_text):
        if not self.context["steam_library_loaded"]:
            return (
                "Primero necesito cargar tu biblioteca de Steam.\n"
                "Pega un SteamID64 con un mensaje como:\n"
                "• cargar steam 7656119XXXXXXXXXX\n\n"
                "Si no puedo leerla, te avisaré de que puede no ser pública."
            )

        filters = self.extractor.extract_filters(clean_text)
        self._update_context(filters)

        rawg_result = self._search_games_rawg(page_size=20)

        owned_games = self.steam_library_manager.recommend_from_library(
            rawg_result,
            self.context["steam_library_map"],
            limit=5,
            prioritize_less_played=True,
        )

        self.context["last_results"] = owned_games
        return self.steam_library_manager.format_library_recommendations(owned_games)

    def _details_from_index(self, text):
        index = self.extractor.extract_index_reference(text)
        if index is None:
            return None

        if not self.context["last_results"]:
            return "No tengo resultados anteriores. Haz primero una búsqueda."

        idx = index - 1
        if idx < 0 or idx >= len(self.context["last_results"]):
            return "Ese número no corresponde a ningún juego de la última búsqueda."

        game = self.context["last_results"][idx]
        details = self.rawg.get_game_details(game["slug"])
        self.context["last_game_slug"] = details.get("slug")
        return format_game_details(details)

    def _details_from_name(self, text):
        candidate = self.extractor.extract_search_candidate(text)
        if not candidate:
            return "Dime el nombre del juego o usa algo como 'detalles del 1'."

        result = self.rawg.search_games(
            search=candidate,
            page_size=1,
            search_precise=True,
            search_exact=False,
        )

        games = result.get("results", [])
        if not games:
            return "No he encontrado ese juego."

        details = self.rawg.get_game_details(games[0]["slug"])
        self.context["last_game_slug"] = details.get("slug")
        return format_game_details(details)

    def respond(self, user_input):
        try:
            clean_text = self.extractor.preprocess_text(user_input)
            intent = detect_intent(clean_text)

            # Cargar biblioteca de Steam
            if "cargar steam" in clean_text or "conectar steam" in clean_text or "steamid" in clean_text:
                steamid = self._extract_steamid(clean_text)
                if not steamid:
                    return (
                        "No he encontrado un SteamID64 válido en tu mensaje.\n"
                        "Usa algo como:\n"
                        "• cargar steam 7656119XXXXXXXXXX"
                    )
                return self._load_steam_library(steamid)

            if intent == "greeting":
                return format_welcome_message()

            if intent == "farewell":
                return format_goodbye_message()

            if intent == "reset":
                self.reset()
                return format_reset_message()

            if intent == "genres":
                genres = self.rawg.get_genres(page_size=50)
                return format_genres_list(genres)

            if intent == "platforms":
                platforms = self.rawg.get_platforms(page_size=50)
                return format_platforms_list(platforms)

            if intent == "help":
                return (
                    format_help_message()
                    + "\n\nSteam:\n"
                    "• cargar steam 7656119XXXXXXXXXX\n"
                    "• recomiendame algo de mi biblioteca\n"
                    "• un rpg de mi biblioteca"
                )

            if intent == "details":
                result = self._details_from_index(clean_text)
                if result:
                    return result
                return self._details_from_name(clean_text)

            # Consultas sobre biblioteca de Steam
            if self._is_library_query(clean_text):
                return self._recommend_from_steam_library(clean_text)

            # Búsqueda general en RAWG
            filters = self.extractor.extract_filters(clean_text)
            self._update_context(filters)

            result = self._search_games_rawg(page_size=5)
            games = result.get("results", [])
            self.context["last_results"] = games

            if not games:
                return format_no_results_message()

            return format_game_list(games, self.context)

        except Exception as e:
            return format_error_message(str(e))