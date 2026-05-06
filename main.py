import re
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
        self.reset()

        # Cargar tu base de conocimiento antigua
        with open("reglas.json", "r", encoding="utf-8") as file:
            rules_data = json.load(file)
            self.rules = [{"conditions": set(r["conditions"]), "conclusions": set(r["conclusions"])} for r in
                          rules_data["rules"]]
            self.keyword_map = rules_data["keyword_map"]

        # TRADUCTOR: De tus perfiles a etiquetas de RAWG
        self.profile_to_rawg = {
            "perfil_chill_solitario": {"genres": "indie,casual", "tags": "singleplayer,relaxing"},
            "perfil_narrativo": {"genres": "adventure,rpg", "tags": "story-rich,singleplayer"},
            "perfil_competitivo_online": {"genres": "action,shooter", "tags": "multiplayer,competitive"},
            "perfil_coop_relajado": {"genres": "indie,casual", "tags": "co-op,multiplayer,relaxing"},
            "perfil_terror_grupo": {"genres": "action,indie", "tags": "horror,co-op,multiplayer"},
            "perfil_estrategia_corta": {"genres": "strategy,board-games", "tags": "turn-based,fast-paced"},
            "perfil_accion_dificil": {"genres": "action", "tags": "difficult,souls-like"},
            "perfil_exploracion_solo": {"genres": "adventure", "tags": "open-world,singleplayer"},
            "perfil_terror_solo": {"genres": "action,adventure", "tags": "horror,singleplayer"},
            "perfil_accion_rapida": {"genres": "action,indie", "tags": "fast-paced,roguelike"},
            "perfil_exploracion_coop": {"genres": "adventure", "tags": "open-world,co-op"},
            "perfil_shooter_coop": {"genres": "shooter", "tags": "co-op"},
            "perfil_coop_historia": {"genres": "adventure,rpg", "tags": "co-op,story-rich"},
            "perfil_estrategia_multi": {"genres": "strategy", "tags": "multiplayer"},
            "perfil_terror_rapido": {"genres": "action", "tags": "horror,fast-paced"},
            "perfil_accion_multi_rapido": {"genres": "action", "tags": "multiplayer,fast-paced"},
            "perfil_estrategia_chill": {"genres": "strategy,casual", "tags": "relaxing,singleplayer"},
            "perfil_estrategia_multi_rapida": {"genres": "strategy", "tags": "multiplayer,fast-paced"},
            "perfil_estrategia_multi_larga": {"genres": "strategy", "tags": "multiplayer,turn-based"},
            "perfil_accion_chill_multi": {"genres": "action,casual", "tags": "multiplayer,relaxing"}
        }
        self.reset()

        # --- RECUPERAMOS TUS FUNCIONES DEL SISTEMA EXPERTO ---

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

    def ask_for_missing_info(self):
        # Miramos qué categorías de datos tenemos
        has_player_count = any(x in self.facts for x in ["solo", "multi"])
        has_vibe = any(x in self.facts for x in ["relajado", "competitivo", "dificil", "poco_tiempo", "mucho_tiempo"])
        has_genre = any(x in self.facts for x in ["historia", "accion", "estrategia", "explorar", "miedo"])

        # Contamos cuántas pistas nos ha dado (máximo 3)
        pistas_dadas = sum([has_player_count, has_vibe, has_genre])

        # Si ya nos ha dado 2 o más pistas, ¡no le agobiamos más!
        # Le asignamos un perfil por defecto basado en lo que sabemos
        if pistas_dadas >= 2:
            if "multi" in self.facts and "competitivo" in self.facts:
                self.facts.add("perfil_competitivo_online")
                return None # Devolvemos None para que el código siga adelante
            elif "accion" in self.facts:
                self.facts.add("perfil_accion_rapida")
                return None
            else:
                self.facts.add("perfil_chill_solitario") # Perfil salvavidas
                return None

        # Solo preguntamos si ha dado muy poca información (0 o 1 pista)
        if not has_player_count: return "Vale, veo por dónde vas. Pero, ¿prefieres jugar en solitario o en multijugador?"
        if not has_vibe: return "Entendido. ¿Buscas algo relajado, un buen reto, o partidas cortas?"
        if not has_genre: return "Casi lo tengo. ¿Qué temática te apetece más: historia, acción, estrategia, explorar o pasar miedo?"

        return "No encuentro un perfil exacto. ¿Podrías darme otras preferencias?"

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

    def respond(self, user_input):
        try:
            clean_text = self.extractor.preprocess_text(user_input)
            intent = detect_intent(clean_text)

            # --- PARTE 1: BLOQUEO DE FUNCIONALIDADES ESPECIALES ---

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
                self.facts.clear()  # Limpiamos también el sistema experto
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

            # --- PARTE 2: LÓGICA DEL SISTEMA EXPERTO ---

            # 1. Extraemos los hechos (palabras clave antiguas) del texto
            new_facts = self.extract_facts(clean_text)
            self.facts.update(new_facts)

            # 2. Si el usuario pide un juego de forma general pero no da ninguna pista
            if not self.facts:
                return "¿Qué tipo de videojuego buscas? Dime tus preferencias para encontrarte el mejor juego ahora mismo."

            # 3. Pensamos (Ejecutamos el motor de inferencia)
            self.forward_chaining()

            # 4. Comprobamos si hemos deducido algún perfil de jugador
            inferred_profiles = [f for f in self.facts if f.startswith("perfil_")]

            # ¡AQUÍ ESTÁ EL CAMBIO DEL NONE!
            # Si no hay perfil, preguntamos lo que falta o forzamos uno
            if not inferred_profiles:
                pregunta = self.ask_for_missing_info()
                if pregunta:
                    # Si nos devuelve texto, es que faltan demasiados datos y hay que preguntar
                    return pregunta
                else:
                    # Si devuelve None, es que ask_for_missing_info ha forzado un perfil salvavidas
                    inferred_profiles = [f for f in self.facts if f.startswith("perfil_")]

            # --- PARTE 3: BÚSQUEDA EN RAWG USANDO EL PERFIL + PLATAFORMAS ---

            # ¡AQUÍ ESTÁ EL CAMBIO DE LAS PLATAFORMAS!
            # Extraemos plataformas u otros filtros extra directamente del texto
            filtros_extra = self.extractor.extract_filters(clean_text)

            # 5. Traducimos el perfil para RAWG
            perfil_principal = inferred_profiles[0]
            rawg_params = self.profile_to_rawg.get(perfil_principal, {})

            # 6. Buscamos en RAWG combinando Perfil + Plataformas extra
            result = self.rawg.search_games(
                genres=rawg_params.get("genres"),
                tags=rawg_params.get("tags"),
                platforms=",".join(str(p) for p in filtros_extra.get("platforms", [])) if filtros_extra.get("platforms") else None,
                ordering="-rating",  # Traemos los mejor valorados
                page_size=5
            )

            games = result.get("results", [])
            self.context["last_results"] = games  # Guardamos para poder pedir "detalles del 1"

            if not games:
                return "Vaya, mi base de datos no tiene juegos ahora mismo para este perfil."

            # Limpiamos los hechos para la siguiente búsqueda
            self.facts.clear()

            # Creamos el contexto falso para que el formatter muestre bien los datos en pantalla
            contexto_formato = {
                "genres": [rawg_params.get("genres", "")],
                "tags": [rawg_params.get("tags", "")],
                "platforms": filtros_extra.get("platforms", []), # Le pasamos las plataformas que haya detectado (ej: móvil)
                "ordering": "-rating"
            }

            return format_game_list(games, contexto_formato)

        except Exception as e:
            return format_error_message(str(e))