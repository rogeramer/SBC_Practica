from rawg_service import RawgService
from chatbot import *

class Gamebot:
    def __init__(self):
        self.rawg = RawgService()
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

    def _search_games(self, page_size=5):
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
                return format_help_message()

            if intent == "details":
                result = self._details_from_index(clean_text)
                if result:
                    return result
                return self._details_from_name(clean_text)

            filters = self.extractor.extract_filters(clean_text)
            self._update_context(filters)

            result = self._search_games(page_size=5)
            games = result.get("results", [])
            self.context["last_results"] = games

            if not games:
                return format_no_results_message()

            return format_game_list(games, self.context)

        except Exception as e:
            return format_error_message(str(e))