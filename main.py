import re
from datetime import date
import json

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

        self.facts = set()

        with open("reglas.json", "r", encoding="utf-8") as file:
            rules_data = json.load(file)
            self.rules = [
                {
                    "conditions": set(r["conditions"]),
                    "conclusions": set(r["conclusions"])
                }
                for r in rules_data["rules"]
            ]
            self.keyword_map = rules_data["keyword_map"]
            self.guides = rules_data["guides"]

        self.profile_to_rawg = {
            "perfil_chill_solitario": {"genres": "indie,casual", "tags": "singleplayer,relaxing"},
            "perfil_narrativo": {
                "genres": "adventure,role-playing-games-rpg",
                "tags": "story-rich,singleplayer"
            },
            "perfil_competitivo_online": {"genres": "action,shooter", "tags": "multiplayer,competitive"},
            "perfil_coop_relajado": {"genres": "indie,casual", "tags": "co-op,multiplayer,relaxing"},
            "perfil_terror_grupo": {"genres": "action,indie", "tags": "horror,co-op,multiplayer"},
            "perfil_estrategia_corta": {"genres": "strategy", "tags": "turn-based"},
            "perfil_accion_dificil": {"genres": "action", "tags": "difficult,souls-like"},
            "perfil_exploracion_solo": {"genres": "adventure", "tags": "open-world,singleplayer"},
            "perfil_terror_solo": {"genres": "action,adventure", "tags": "horror,singleplayer"},
            "perfil_accion_rapida": {"genres": "action,indie", "tags": "fast-paced,roguelike"},
            "perfil_exploracion_coop": {"genres": "adventure", "tags": "open-world,co-op"},
            "perfil_shooter_coop": {"genres": "shooter", "tags": "co-op"},
            "perfil_coop_historia": {
                "genres": "adventure,role-playing-games-rpg",
                "tags": "co-op,story-rich"
            },
            "perfil_estrategia_multi": {"genres": "strategy", "tags": "multiplayer"},
            "perfil_terror_rapido": {"genres": "action", "tags": "horror,fast-paced"},
            "perfil_accion_multi_rapido": {"genres": "action", "tags": "multiplayer,fast-paced"},
            "perfil_estrategia_chill": {"genres": "strategy,casual", "tags": "relaxing,singleplayer"},
            "perfil_estrategia_multi_rapida": {"genres": "strategy", "tags": "multiplayer,fast-paced"},
            "perfil_estrategia_multi_larga": {"genres": "strategy", "tags": "multiplayer,turn-based"},
            "perfil_accion_chill_multi": {"genres": "action,casual", "tags": "multiplayer,relaxing"},
        }
        self.platform_map = {
                    "android": 21,
                    "mobile": 21,
                    "mobil": 21,
                    "movil": 21,
                    "móvil": 21,
                    "pc": 4,
                    "linux": 6,
                    "windows": 4,
                    "playstation": 187,
                    "ps": 187,
                    "xbox": 1,
                    "switch": 7,
                }
        self.reset()

    def can_recommend_now(self, steam_mode=False):
        """
        Decide si ya hay suficiente información para recomendar.

        No todas las pistas tienen el mismo peso:
        - Un género explícito ya es suficiente.
        - Un estilo concreto también puede ser suficiente.
        - Jugar con amigos, por sí solo, todavía necesita una aclaración.
        """

        genre = self.user_preferences["genre"]
        mode = self.user_preferences["mode"]
        mood = self.user_preferences["mood"]
        platform = self.user_preferences["platform"]

        strong_tags = {
            "story-rich",
            "horror",
            "relaxing",
            "competitive",
            "difficult",
            "open-world",
            "co-op",
        }

        detected_strong_tags = strong_tags.intersection(
            set(self.context["tags"])
        )

        # Un género explícito permite buscar directamente.
        if genre:
            return True

        # Un estilo claro también permite recomendar directamente.
        if mood:
            return True

        # Algunas etiquetas son suficientemente específicas.
        if detected_strong_tags:
            return True

        # En la búsqueda general, modo + plataforma ya permiten buscar.
        # En Steam no utilizamos la plataforma como requisito.
        if not steam_mode and mode and platform:
            return True

        return False

    def extract_facts(self, text):
        detected = set()
        for phrase, fact in self.keyword_map.items():
            if phrase in text:
                detected.add(fact)
        return detected

    def forward_chaining(self):
        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                if rule["conditions"].issubset(self.facts):
                    for conclusion in rule["conclusions"]:
                        if conclusion not in self.facts:
                            self.facts.add(conclusion)
                            changed = True

    def _select_inferred_profile(self):
        """
        Selecciona el perfil inferido más específico según prioridad.

        El sistema experto puede generar varios perfiles a la vez.
        Este método escoge el más relevante para la búsqueda RAWG.
        """

        inferred_profiles = [
            fact
            for fact in self.facts
            if fact.startswith("perfil_")
        ]

        priority_profiles = [
            "perfil_competitivo_online",
            "perfil_shooter_coop",
            "perfil_accion_multi_rapido",
            "perfil_coop_relajado",
            "perfil_accion_dificil",
            "perfil_accion_rapida",
            "perfil_narrativo",
            "perfil_terror_grupo",
            "perfil_terror_solo",
            "perfil_exploracion_coop",
            "perfil_exploracion_solo",
            "perfil_estrategia_multi_rapida",
            "perfil_estrategia_multi_larga",
            "perfil_estrategia_multi",
            "perfil_estrategia_chill",
            "perfil_estrategia_corta",
            "perfil_accion_chill_multi",
            "perfil_chill_solitario",
        ]

        for profile in priority_profiles:
            if profile in inferred_profiles:
                return profile

        return None

    def _recommend_general_from_preferences(self, clean_text):
        """
        Recomienda juegos RAWG utilizando:
        1. preferencias explícitas;
        2. sistema experto como apoyo;
        3. validación y ranking local.
        """

        new_facts = self.extract_facts(clean_text)
        self.facts.update(new_facts)
        self.forward_chaining()

        profile = self._select_inferred_profile()

        if profile:
            rawg_params = self.profile_to_rawg.get(profile, {})

            # El perfil solo completa filtros ausentes.
            if not self.context["genres"] and rawg_params.get("genres"):
                self.context["genres"] = rawg_params["genres"].split(",")

            if not self.context["tags"] and rawg_params.get("tags"):
                self.context["tags"] = rawg_params["tags"].split(",")

        # Pedimos más candidatos para poder filtrar localmente.
        result = self._search_games_rawg(page_size=40)

        candidates = result.get("results", [])

        games = self._rank_general_candidates(
            candidates
        )[:5]

        self.context["last_results"] = games

        if not games:
            response = (
                "No he encontrado juegos publicados que encajen exactamente "
                "con esos criterios.\n\n"
                "Prueba a simplificar la búsqueda. Por ejemplo:\n"
                "• un RPG\n"
                "• algo competitivo\n"
                "• un juego relajado para móvil"
            )

            self._clear_recommendation_preferences()

            return response

        response = format_game_list(
            games,
            self.context
        )

        self._clear_recommendation_preferences()

        return response

    def ask_for_missing_info(self, steam_mode=False):
        """
        Formula una única pregunta útil.

        En Steam no pregunta plataforma porque la recomendación ya está
        restringida a la biblioteca del usuario.
        """

        genre = self.user_preferences["genre"]
        mode = self.user_preferences["mode"]
        mood = self.user_preferences["mood"]
        platform = self.user_preferences["platform"]

        if mode == "multiplayer" and not mood and not genre:
            return (
                "¿Qué tipo de experiencia buscas para jugar con otras personas? "
                "Por ejemplo: cooperativa, competitiva, relajada o difícil."
            )

        if not genre and not mood:
            return (
                "¿Qué tipo de experiencia buscas? "
                "Por ejemplo: RPG, acción, estrategia, terror, "
                "algo relajado, competitivo o difícil."
            )

        # La plataforma puede ayudar a refinar búsquedas generales,
        # pero no debe bloquear una recomendación si ya hay filtros útiles.
        if not steam_mode and not platform:
            return (
                "Puedo recomendarte opciones para varias plataformas. "
                "También puedes indicarme una concreta: PC, móvil, "
                "PlayStation, Xbox o Switch."
            )

        return None

    def reset(self):
        self.state = "ASKING"

        self.user_preferences = {
            "platform": None,
            "mode": None,
            "mood": None,
            "genre": None,
        }

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
            "steam_recommendation_mode": False,
            "steam_guided_mode": False,
        }

    def _merge_unique(self, current_values, new_values):
        return list(dict.fromkeys(current_values + new_values))

    def _update_context(self, filters):
        if filters.get("search"):
            self.context["search"] = filters["search"]

        if filters.get("genres"):
            self.context["genres"] = self._merge_unique(
                self.context["genres"],
                filters["genres"]
            )

        if filters.get("tags"):
            self.context["tags"] = self._merge_unique(
                self.context["tags"],
                filters["tags"]
            )

        if filters.get("platforms"):
            self.context["platforms"] = self._merge_unique(
                self.context["platforms"],
                filters["platforms"]
            )

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

    def _get_game_genres(self, game):
        """
        Devuelve géneros RAWG normalizados utilizando slug y nombre.
        """
        genres = set()

        for genre in game.get("genres", []):
            slug = (genre.get("slug") or "").lower()
            name = (genre.get("name") or "").lower()

            if slug:
                genres.add(slug)

            if name:
                genres.add(name)

        return genres

    def _get_game_tags(self, game):
        """
        Devuelve etiquetas RAWG normalizadas utilizando slug y nombre.
        """
        tags = set()

        for tag in game.get("tags", []):
            slug = (tag.get("slug") or "").lower()
            name = (tag.get("name") or "").lower()

            if slug:
                tags.add(slug)

            if name:
                tags.add(name)

        return tags

    def _get_game_platform_ids(self, game):
        """
        Obtiene los identificadores RAWG de las plataformas disponibles.
        """
        platform_ids = set()

        for platform_data in game.get("platforms", []):
            platform = platform_data.get("platform", {})
            platform_id = platform.get("id")

            if platform_id is not None:
                platform_ids.add(platform_id)

        return platform_ids

    def _is_released_game(self, game):
        """
        Evita recomendar títulos todavía no publicados o sin fecha conocida.
        """
        released = game.get("released")

        if not released:
            return False

        return released <= date.today().isoformat()

    def _matches_explicit_preferences(self, game):
        """
        Comprueba si el juego satisface las preferencias importantes.

        Los perfiles inferidos ayudan a ampliar la búsqueda, pero las
        preferencias explícitas del usuario tienen prioridad.
        """

        game_genres = self._get_game_genres(game)
        game_tags = self._get_game_tags(game)
        game_platforms = self._get_game_platform_ids(game)

        requested_genres = set(self.context["genres"])
        requested_tags = set(self.context["tags"])
        requested_platforms = set(self.context["platforms"])

        # El juego debe coincidir al menos con uno de los géneros solicitados.
        if requested_genres and not requested_genres.intersection(game_genres):
            return False

        # Si se especifica plataforma, debe estar disponible.
        if requested_platforms and not requested_platforms.intersection(game_platforms):
            return False

        # Validaciones estrictas para preferencias claras.
        strong_tags = {
            "story-rich",
            "horror",
            "relaxing",
            "competitive",
            "difficult",
            "open-world",
            "co-op",
        }

        required_strong_tags = requested_tags.intersection(strong_tags)

        if required_strong_tags and not required_strong_tags.issubset(game_tags):
            return False

        # Multiplayer acepta juegos etiquetados como multiplayer o co-op.
        if "multiplayer" in requested_tags:
            if not {"multiplayer", "co-op"}.intersection(game_tags):
                return False

        # Singleplayer debe aparecer explícitamente.
        if "singleplayer" in requested_tags:
            if "singleplayer" not in game_tags:
                return False

        return True

    def _calculate_game_score(self, game):
        """
        Calcula una puntuación local para ordenar resultados válidos.
        """

        game_genres = self._get_game_genres(game)
        game_tags = self._get_game_tags(game)
        game_platforms = self._get_game_platform_ids(game)

        requested_genres = set(self.context["genres"])
        requested_tags = set(self.context["tags"])
        requested_platforms = set(self.context["platforms"])

        score = 0.0

        # Las coincidencias semánticas pesan más que el rating.
        score += 5 * len(requested_genres.intersection(game_genres))
        score += 4 * len(requested_tags.intersection(game_tags))
        score += 2 * len(requested_platforms.intersection(game_platforms))

        # El rating RAWG actúa como criterio secundario.
        score += float(game.get("rating") or 0)

        # Se premia ligeramente que existan valoraciones suficientes.
        ratings_count = int(game.get("ratings_count") or 0)
        score += min(ratings_count / 1000, 3)

        return score

    def _rank_general_candidates(self, games):
        """
        Filtra y ordena candidatos RAWG antes de mostrarlos.
        """

        valid_games = []

        for game in games:
            if not self._is_released_game(game):
                continue

            if not self._matches_explicit_preferences(game):
                continue

            valid_games.append(game)

        valid_games.sort(
            key=self._calculate_game_score,
            reverse=True
        )

        return valid_games

    def _save_preferences(self, text):
        """
        Extrae preferencias del mensaje y las acumula en el contexto.

        Separa conceptos distintos:
        - RPG es un género.
        - Historia es una etiqueta narrativa.
        - Terror se gestiona como etiqueta.
        - Modo de juego y estilo se almacenan por separado.
        """

        text = text.lower()

        # -------------------------
        # PLATAFORMAS
        # -------------------------
        for keyword, platform_id in self.platform_map.items():
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                self.user_preferences["platform"] = platform_id

        if self.user_preferences["platform"]:
            self.context["platforms"] = [
                self.user_preferences["platform"]
            ]

        # -------------------------
        # GÉNEROS
        # -------------------------
        genre_aliases = {
            "rpg": "role-playing-games-rpg",
            "rol": "role-playing-games-rpg",
            "accion": "action",
            "action": "action",
            "aventura": "adventure",
            "adventure": "adventure",
            "estrategia": "strategy",
            "strategy": "strategy",
            "simulacion": "simulation",
            "simulation": "simulation",
            "puzzle": "puzzle",
            "deportes": "sports",
            "sports": "sports",
            "carreras": "racing",
            "racing": "racing",
            "shooter": "shooter",
        }

        for keyword, slug in genre_aliases.items():
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                self.user_preferences["genre"] = slug

                if slug not in self.context["genres"]:
                    self.context["genres"].append(slug)

        # -------------------------
        # NARRATIVA
        # -------------------------
        narrative_words = [
            "historia",
            "narrativo",
            "narrativa",
            "story",
            "story rich",
        ]

        if any(word in text for word in narrative_words):
            if "story-rich" not in self.context["tags"]:
                self.context["tags"].append("story-rich")

            self.facts.add("historia")

        cooperative_words = [
            "coop",
            "co-op",
            "cooperativo",
            "cooperativa",
            "cooperatiu",
            "cooperativa",
        ]

        if any(word in text for word in cooperative_words):
            self.user_preferences["mode"] = "multiplayer"

            if "multiplayer" not in self.context["tags"]:
                self.context["tags"].append("multiplayer")

            if "co-op" not in self.context["tags"]:
                self.context["tags"].append("co-op")

            self.facts.add("multi")



        # -------------------------
        # MULTIJUGADOR / SOLITARIO
        # -------------------------
        multiplayer_words = [
            "multi",
            "multiplayer",
            "coop",
            "co-op",
            "cooperativo",
            "cooperativa",
            "amics",
            "amic",
            "amigos",
            "amigo",
            "friends",
            "friend",
            "multijugador",
            "cooperatiu",
        ]

        if any(word in text for word in multiplayer_words):
            self.user_preferences["mode"] = "multiplayer"

            if "multiplayer" not in self.context["tags"]:
                self.context["tags"].append("multiplayer")

            self.facts.add("multi")

        if re.search(
                r"\b(solo|solitario|solitari|singleplayer|single)\b",
                text
        ):
            self.user_preferences["mode"] = "singleplayer"

            if "singleplayer" not in self.context["tags"]:
                self.context["tags"].append("singleplayer")

            self.facts.add("solo")

        # -------------------------
        # ESTILO DE JUEGO
        # -------------------------
        relax_words = [
            "relaj",
            "relax",
            "chill",
            "tranquilo",
            "tranquila",
            "calmado",
            "calmada",
            "relaxing",
            "relaxat",
            "relaxada",
        ]

        if any(word in text for word in relax_words):
            self.user_preferences["mood"] = "relaxing"

            if "relaxing" not in self.context["tags"]:
                self.context["tags"].append("relaxing")

            self.facts.add("relajado")

        competitive_words = [
            "compet",
            "rank",
            "ranking",
            "pvp",
        ]

        if any(word in text for word in competitive_words):
            self.user_preferences["mood"] = "competitive"

            if "competitive" not in self.context["tags"]:
                self.context["tags"].append("competitive")

            self.facts.add("competitivo")

        hard_words = [
            "dific",
            "hard",
            "souls",
            "reto",
            "desafio",
        ]

        if any(word in text for word in hard_words):
            self.user_preferences["mood"] = "difficult"

            if "difficult" not in self.context["tags"]:
                self.context["tags"].append("difficult")

            self.facts.add("dificil")

        # -------------------------
        # TEMÁTICAS Y ETIQUETAS
        # -------------------------
        if any(word in text for word in ["terror", "miedo", "horror"]):
            if "horror" not in self.context["tags"]:
                self.context["tags"].append("horror")

            self.facts.add("miedo")

        if any(word in text for word in [
            "explorar",
            "exploracion",
            "open world",
            "mundo abierto",
        ]):
            if "open-world" not in self.context["tags"]:
                self.context["tags"].append("open-world")

            self.facts.add("explorar")

        # -------------------------
        # RESPUESTAS ABIERTAS
        # -------------------------
        if any(word in text for word in [
            "me da igual",
            "da igual",
            "cualquiera",
            "no importa",
            "whatever",
        ]):
            # Solo se usa PC como valor por defecto para la búsqueda general.
            self.user_preferences["platform"] = 4
            self.context["platforms"] = [4]


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

    def _recommend_from_steam_library(self, clean_text):
        """
        Recomienda únicamente juegos poseídos por el usuario.

        No pregunta plataforma porque Steam ya define el ámbito
        de la biblioteca personal.
        """

        if not self.context["steam_library_loaded"]:
            return (
                "Primero necesito cargar tu biblioteca de Steam.\n"
                "Pega un SteamID64 con un mensaje como:\n"
                "• cargar steam 7656119XXXXXXXXXX\n\n"
                "Si no puedo leerla, te avisaré de que puede no ser pública."
            )

        self.context["steam_recommendation_mode"] = True

        self._save_preferences(clean_text)

        filters = self.extractor.extract_filters(clean_text)

        # Evitamos que RAWG busque literalmente frases como:
        # "recomiendame algo de mi biblioteca".
        filters["search"] = None
        filters["platforms"] = []

        self.context["search"] = None
        self.context["platforms"] = []

        self._update_context(filters)

        if not self.can_recommend_now(steam_mode=True):
            return self.ask_for_missing_info(steam_mode=True)

        rawg_result = self._search_games_rawg(page_size=100)

        owned_games = self.steam_library_manager.recommend_from_library(
            rawg_result,
            self.context["steam_library_map"],
            limit=5,
            prioritize_less_played=True,
        )

        self.context["last_results"] = owned_games
        self.context["steam_recommendation_mode"] = False
        self.context["steam_guided_mode"] = False

        response = self.steam_library_manager.format_library_recommendations(
            owned_games
        )

        # Conservamos last_results y la biblioteca, pero limpiamos
        # los filtros de la petición anterior.
        self._clear_recommendation_preferences()

        return response


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
            return "Dime el nombre del juego del que quieres saber más."

        candidate_lower = candidate.lower()

        # 1. MEMORIA: Buscamos primero en los juegos que acabamos de recomendar
        if self.context.get("last_results"):
            for game in self.context["last_results"]:
                game_name_lower = game.get("name", "").lower()

                # Si el candidato está dentro del nombre (ej: "system" en "System Shock 2")
                # o el nombre está dentro del candidato, es un match directo.
                if candidate_lower in game_name_lower or game_name_lower in candidate_lower:
                    details = self.rawg.get_game_details(game["slug"])
                    self.context["last_game_slug"] = details.get("slug")
                    return format_game_details(details)

        # 2. Si no estaba en la última recomendación, lo buscamos en RAWG general
        result = self.rawg.search_games(
            search=candidate,
            page_size=1,
            search_precise=True,
            search_exact=False,
        )

        games = result.get("results", [])

        if not games:
            return f"No he encontrado ningún juego que se llame exactamente '{candidate}'."

        details = self.rawg.get_game_details(games[0]["slug"])
        self.context["last_game_slug"] = details.get("slug")
        return format_game_details(details)

    def _clear_recommendation_preferences(self):
        """
        Limpia únicamente los filtros temporales de recomendación.

        Mantiene:
        - biblioteca Steam cargada;
        - SteamID;
        - últimos resultados para poder pedir detalles.
        """

        self.user_preferences = {
            "platform": None,
            "mode": None,
            "mood": None,
            "genre": None,
        }

        self.context["search"] = None
        self.context["genres"] = []
        self.context["tags"] = []
        self.context["platforms"] = []
        self.context["dates"] = None
        self.context["metacritic"] = None
        self.context["steam_recommendation_mode"] = False
        self.context["steam_guided_mode"] = False

        self.facts.clear()


    def respond(self, user_input):
        try:
            clean_text = self.extractor.preprocess_text(user_input)
            intent = detect_intent(clean_text)

            # =========================================================
            # 1. CARGAR STEAM Y PROCESAR ACCIONES COMBINADAS
            # =========================================================
            steamid = self._extract_steamid(clean_text)

            if steamid and "steam" in clean_text:
                load_message = self._load_steam_library(steamid)

                if not self.context["steam_library_loaded"]:
                    return load_message

                # Ejemplo:
                # "Carga Steam 7656... y dime mis juegos más jugados"
                if intent == "most_played":
                    games = sorted(
                        self.context["steam_library"],
                        key=lambda game: game.get("playtime_forever", 0),
                        reverse=True
                    )[:10]

                    if not games:
                        return (
                            f"{load_message}\n\n"
                            "No he encontrado juegos en tu biblioteca."
                        )

                    response = "🎮 Tus juegos más jugados son:\n\n"

                    for index, game in enumerate(games, start=1):
                        hours = round(
                            game.get("playtime_forever", 0) / 60,
                            1
                        )

                        response += (
                            f"{index}. {game['name']} "
                            f"({hours} horas)\n"
                        )

                    return (
                        f"{load_message}\n\n"
                        f"{response}"
                    )

                # Ejemplo:
                # "Carga Steam 7656... y recomiéndame un RPG de mi biblioteca"
                if self._is_library_query(clean_text):
                    self._clear_recommendation_preferences()

                    recommendation = (
                        self._recommend_from_steam_library(
                            clean_text
                        )
                    )

                    return (
                        f"{load_message}\n\n"
                        f"{recommendation}"
                    )

                return load_message

            # SteamID inválido
            if (
                    "cargar steam" in clean_text
                    or "carga steam" in clean_text
                    or "conectar steam" in clean_text
                    or "steamid" in clean_text
            ):
                if not steamid:
                    return (
                        "No he encontrado un SteamID64 válido en tu mensaje.\n"
                        "Usa algo como:\n"
                        "• cargar steam 7656119XXXXXXXXXX"
                    )

            # =========================================================
            # 2. INTENCIONES GENERALES
            # =========================================================
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
                          "• un rpg de mi biblioteca\n"
                          "• dime mis juegos más jugados"
                )

            # =========================================================
            # 3. GUÍAS
            # =========================================================
            if intent == "guide":
                candidate = self.extractor.extract_search_candidate(
                    clean_text
                )

                if not candidate:
                    return "¿De qué juego quieres una guía?"

                candidate = candidate.lower()

                for game_name, tips in self.guides.items():
                    if game_name in candidate:
                        formatted_tips = "\n".join(
                            f"• {tip}"
                            for tip in tips
                        )

                        return (
                            f"🎮 Guía básica de {game_name.title()}:\n\n"
                            f"{formatted_tips}"
                        )

                return f"No tengo guía para {candidate}."

            # =========================================================
            # 4. RANKING STEAM
            # =========================================================
            if intent == "most_played":
                if not self.context["steam_library_loaded"]:
                    return (
                        "Primero debes cargar tu biblioteca de Steam.\n"
                        "Ejemplo:\n"
                        "• cargar steam 7656119XXXXXXXXXX"
                    )

                games = sorted(
                    self.context["steam_library"],
                    key=lambda game: game.get(
                        "playtime_forever",
                        0
                    ),
                    reverse=True
                )[:10]

                if not games:
                    return "No he encontrado juegos en tu biblioteca."

                response = "🎮 Tus juegos más jugados son:\n\n"

                for index, game in enumerate(games, start=1):
                    hours = round(
                        game.get("playtime_forever", 0) / 60,
                        1
                    )

                    response += (
                        f"{index}. {game['name']} "
                        f"({hours} horas)\n"
                    )

                return response

            # =========================================================
            # 5. DETALLES DE UN JUEGO
            # =========================================================
            if intent == "details":
                result = self._details_from_index(clean_text)

                if result:
                    return result

                return self._details_from_name(clean_text)

            # =========================================================
            # 6. TOP JUEGOS PARA MÓVIL
            # =========================================================
            if intent == "top_games":
                result = self.rawg.search_games(
                    platforms="21",
                    ordering="-rating",
                    page_size=30
                )

                games = result.get("results", [])
                filtered_games = []

                for game in games:
                    tags = [
                        tag["name"].lower()
                        for tag in game.get("tags", [])
                    ]

                    if (
                            "multiplayer" in tags
                            or "co-op" in tags
                    ):
                        filtered_games.append(game)

                games = filtered_games[:5]
                self.context["last_results"] = games

                safe_context = {
                    "genres": [],
                    "tags": [],
                    "platforms": [21],
                    "ordering": "-rating",
                }

                return format_game_list(
                    games,
                    safe_context
                )

            # =========================================================
            # 7. RECOMENDACIONES DE BIBLIOTECA STEAM
            # =========================================================
            if self._is_library_query(clean_text):
                self._clear_recommendation_preferences()

                return self._recommend_from_steam_library(
                    clean_text
                )

            # Continuar una pregunta iniciada en el modo Steam
            if self.context["steam_recommendation_mode"]:
                return self._recommend_from_steam_library(
                    clean_text
                )

            # =========================================================
            # 8. RECOMENDACIÓN GENERAL RAWG
            # =========================================================
            self._save_preferences(clean_text)

            filters = self.extractor.extract_filters(
                clean_text
            )

            # Evitar búsquedas literales de frases conversacionales.
            filters["search"] = None

            self._update_context(filters)

            if self.can_recommend_now(steam_mode=False):
                return self._recommend_general_from_preferences(
                    clean_text
                )

            has_any_preference = any([
                self.user_preferences["platform"],
                self.user_preferences["mode"],
                self.user_preferences["mood"],
                self.user_preferences["genre"],
                self.context["tags"],
                self.context["genres"],
            ])

            if not has_any_preference:
                return (
                    "¿Qué tipo de experiencia buscas? 🤔\n\n"
                    "Por ejemplo:\n"
                    "• Quiero un RPG con historia\n"
                    "• Busco algo competitivo para jugar con amigos\n"
                    "• Quiero algo relajado para móvil\n"
                    "• Quiero un juego de terror\n"
                    "• Recomiéndame algo de mi biblioteca"
                )

            return self.ask_for_missing_info(
                steam_mode=False
            )

        except Exception as e:
            return format_error_message(str(e))