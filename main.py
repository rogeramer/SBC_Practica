import json
import re
from pathlib import Path

from rawg_service import RawgService
from steam_service import SteamService
from steam_library import SteamLibraryManager

from chatbot.intent_parser import detect_intent
from chatbot.filtres import FilterExtractor
from chatbot.recommendation_config import (
    PLATFORM_MAP,
    PROFILE_PRIORITY,
)
from chatbot.recommendation_engine import (
    RecommendationEngine,
)
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
    """
    Coordinador principal del chatbot.

    Este archivo gestiona:
    - conversación;
    - memoria temporal;
    - forward chaining;
    - resolución de conflictos;
    - selección del flujo RAWG o Steam.

    El ranking heurístico se delega en RecommendationEngine.
    """

    def __init__(self):
        self.rawg = RawgService()
        self.steam = SteamService()

        self.steam_library_manager = SteamLibraryManager(
            self.steam,
            self.rawg,
        )

        self.extractor = FilterExtractor(
            self.rawg
        )

        self.recommender = RecommendationEngine(
            self.rawg
        )

        self.profile_priority = PROFILE_PRIORITY
        self.platform_map = PLATFORM_MAP

        self.facts = set()

        self._load_knowledge_base()
        self.reset()

    # =========================================================
    # BASE DE CONOCIMIENTO
    # =========================================================

    def _load_knowledge_base(self):
        """
        Carga reglas, palabras clave y guías desde reglas.json.
        """

        rules_path = (
            Path(__file__)
            .resolve()
            .with_name("reglas.json")
        )

        with rules_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            rules_data = json.load(file)

        self.rules = [
            {
                "conditions": set(
                    rule.get(
                        "conditions",
                        [],
                    )
                ),
                "conclusions": set(
                    rule.get(
                        "conclusions",
                        [],
                    )
                ),
            }
            for rule in rules_data.get(
                "rules",
                [],
            )
        ]

        # Normalizar las expresiones para compararlas
        # con el texto preprocesado del usuario.
        self.keyword_map = {
            self.extractor.preprocess_text(
                phrase
            ): fact
            for phrase, fact in rules_data.get(
                "keyword_map",
                {},
            ).items()
        }

        # Conservar el nombre original para mostrarlo en pantalla.
        self.guides = {
            self.extractor.preprocess_text(
                game_name
            ): {
                "name": game_name,
                "content": content,
            }
            for game_name, content in rules_data.get(
                "guides",
                {},
            ).items()
        }

    # =========================================================
    # SISTEMA EXPERTO
    # =========================================================

    def extract_facts(self, text):
        """
        Detecta hechos explícitos utilizando keyword_map.
        """

        detected_facts = set()

        for phrase, fact in self.keyword_map.items():
            pattern = (
                rf"(?<!\w)"
                rf"{re.escape(phrase)}"
                rf"(?!\w)"
            )

            if re.search(
                pattern,
                text,
            ):
                detected_facts.add(fact)

        return detected_facts

    def forward_chaining(self):
        """
        Aplica reglas repetidamente hasta que no aparezcan
        conclusiones nuevas.
        """

        changed = True

        while changed:
            changed = False

            for rule in self.rules:
                conditions = rule[
                    "conditions"
                ]

                conclusions = rule[
                    "conclusions"
                ]

                if not conditions.issubset(
                    self.facts
                ):
                    continue

                for conclusion in conclusions:
                    if conclusion not in self.facts:
                        self.facts.add(
                            conclusion
                        )

                        changed = True

    def _select_inferred_profile(self):
        """
        Resuelve conflictos entre perfiles aplicando:

        1. especificidad;
        2. prioridad manual;
        3. orden estable.
        """

        candidates = []

        for rule in self.rules:
            conditions = rule.get(
                "conditions",
                set(),
            )

            conclusions = rule.get(
                "conclusions",
                set(),
            )

            if not conditions.issubset(
                self.facts
            ):
                continue

            for conclusion in conclusions:
                if not conclusion.startswith(
                    "perfil_"
                ):
                    continue

                candidates.append({
                    "profile": conclusion,
                    "specificity": len(
                        conditions
                    ),
                    "priority": (
                        self.profile_priority.get(
                            conclusion,
                            0,
                        )
                    ),
                })

        # Permitir perfiles añadidos manualmente
        # aunque no procedan directamente de una regla.
        if not candidates:
            for fact in self.facts:
                if fact.startswith(
                    "perfil_"
                ):
                    candidates.append({
                        "profile": fact,
                        "specificity": 0,
                        "priority": (
                            self.profile_priority.get(
                                fact,
                                0,
                            )
                        ),
                    })

        if not candidates:
            return None

        candidates.sort(
            key=lambda candidate: (
                candidate[
                    "specificity"
                ],
                candidate[
                    "priority"
                ],
                candidate[
                    "profile"
                ],
            ),
            reverse=True,
        )

        return candidates[0][
            "profile"
        ]

    # =========================================================
    # MEMORIA CONVERSACIONAL
    # =========================================================

    def reset(self):
        """
        Reinicia la conversación completa.

        También elimina la biblioteca Steam cargada.
        """

        self.facts.clear()

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
        }

    def _merge_unique(
        self,
        current_values,
        new_values,
    ):
        """
        Combina listas sin duplicados y conserva el orden.
        """

        return list(
            dict.fromkeys(
                current_values
                + new_values
            )
        )

    def _update_context(self, filters):
        """
        Acumula filtros durante una conversación guiada.
        """

        if filters.get("search"):
            self.context["search"] = filters[
                "search"
            ]

        if filters.get("genres"):
            self.context["genres"] = (
                self._merge_unique(
                    self.context[
                        "genres"
                    ],
                    filters[
                        "genres"
                    ],
                )
            )

        if filters.get("tags"):
            self.context["tags"] = (
                self._merge_unique(
                    self.context[
                        "tags"
                    ],
                    filters[
                        "tags"
                    ],
                )
            )

        if filters.get("platforms"):
            self.context[
                "platforms"
            ] = self._merge_unique(
                self.context[
                    "platforms"
                ],
                filters[
                    "platforms"
                ],
            )

        if filters.get("ordering"):
            self.context["ordering"] = filters[
                "ordering"
            ]

        if filters.get("dates"):
            self.context["dates"] = filters[
                "dates"
            ]

        if filters.get("metacritic"):
            self.context[
                "metacritic"
            ] = filters[
                "metacritic"
            ]

    def _clear_recommendation_preferences(self):
        """
        Limpia filtros temporales después de recomendar.

        Mantiene:
        - biblioteca Steam;
        - SteamID;
        - últimos resultados para pedir detalles.
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
        self.context["ordering"] = "-rating"
        self.context["dates"] = None
        self.context["metacritic"] = None
        self.context[
            "steam_recommendation_mode"
        ] = False

        self.facts.clear()

    # =========================================================
    # EXTRACCIÓN DE PREFERENCIAS CONVERSACIONALES
    # =========================================================

    def _contains_any_phrase(
        self,
        text,
        phrases,
    ):
        """
        Comprueba expresiones completas.
        """

        for phrase in phrases:
            pattern = (
                rf"(?<!\w)"
                rf"{re.escape(phrase)}"
                rf"(?!\w)"
            )

            if re.search(
                pattern,
                text,
            ):
                return True

        return False

    def _save_preferences(self, text):
        """
        Extrae filtros y preferencias conversacionales.

        Devuelve los filtros para evitar procesar el texto
        varias veces innecesariamente.
        """

        filters = self.extractor.extract_filters(
            text
        )

        self._update_context(
            filters
        )

        # -------------------------
        # PLATAFORMA
        # -------------------------

        if filters.get("platforms"):
            self.user_preferences[
                "platform"
            ] = filters[
                "platforms"
            ][-1]

        # -------------------------
        # GÉNERO
        # -------------------------

        if filters.get("genres"):
            self.user_preferences[
                "genre"
            ] = filters[
                "genres"
            ][-1]

        tags = set(
            self.context[
                "tags"
            ]
        )

        # -------------------------
        # NARRATIVA
        # -------------------------

        if "story-rich" in tags:
            self.facts.add(
                "historia"
            )

        # -------------------------
        # COOPERATIVO
        # -------------------------

        cooperative_tags = {
            "co-op",
            "online-co-op",
            "local-co-op",
            "split-screen",
        }

        if cooperative_tags.intersection(
            tags
        ):
            self.user_preferences[
                "mode"
            ] = "co-op"

            if "co-op" not in self.context[
                "tags"
            ]:
                self.context[
                    "tags"
                ].append(
                    "co-op"
                )

            if "multiplayer" not in self.context[
                "tags"
            ]:
                self.context[
                    "tags"
                ].append(
                    "multiplayer"
                )

            self.facts.add(
                "multi"
            )
            
            self.facts.add(
                "coop"
            )

        # -------------------------
        # MULTIJUGADOR GENÉRICO
        # -------------------------

        friend_words = [
            "amigo",
            "amigos",
            "amic",
            "amics",
            "friends",
            "friend",
        ]

        is_multiplayer = (
            "multiplayer" in tags
            or self._contains_any_phrase(
                text,
                friend_words,
            )
        )

        if (
            is_multiplayer
            and self.user_preferences[
                "mode"
            ] != "co-op"
        ):
            self.user_preferences[
                "mode"
            ] = "multiplayer"

            if "multiplayer" not in self.context[
                "tags"
            ]:
                self.context[
                    "tags"
                ].append(
                    "multiplayer"
                )

            self.facts.add(
                "multi"
            )

        # -------------------------
        # SOLITARIO
        # -------------------------

        if "singleplayer" in tags:
            self.user_preferences[
                "mode"
            ] = "singleplayer"

            self.facts.add(
                "solo"
            )

        # -------------------------
        # ESTILO
        # -------------------------

        if "relaxing" in tags:
            self.user_preferences[
                "mood"
            ] = "relaxing"

            self.facts.add(
                "relajado"
            )

        if "competitive" in tags:
            self.user_preferences[
                "mood"
            ] = "competitive"

            self.facts.add(
                "competitivo"
            )

        if "difficult" in tags:
            self.user_preferences[
                "mood"
            ] = "difficult"

            self.facts.add(
                "dificil"
            )

        # -------------------------
        # TEMÁTICAS
        # -------------------------

        if "horror" in tags:
            self.facts.add(
                "miedo"
            )

        if "open-world" in tags:
            self.facts.add(
                "explorar"
            )

        # -------------------------
        # RESPUESTAS ABIERTAS
        # -------------------------

        open_answers = [
            "me da igual",
            "da igual",
            "cualquiera",
            "no importa",
            "whatever",
        ]

        if self._contains_any_phrase(
            text,
            open_answers,
        ):
            self.user_preferences[
                "platform"
            ] = 4

            self.context[
                "platforms"
            ] = [4]

        return filters

    # =========================================================
    # DECISIÓN CONVERSACIONAL
    # =========================================================

    def can_recommend_now(
        self,
        steam_mode=False,
    ):
        """
        Determina si ya hay suficientes pistas.
        """

        genre = self.user_preferences[
            "genre"
        ]

        mode = self.user_preferences[
            "mode"
        ]

        mood = self.user_preferences[
            "mood"
        ]

        platform = self.user_preferences[
            "platform"
        ]

        strong_tags = {
            "story-rich",
            "horror",
            "relaxing",
            "competitive",
            "difficult",
            "open-world",
            "co-op",
            "online-co-op",
            "local-co-op",
            "split-screen",
        }

        detected_strong_tags = (
            strong_tags.intersection(
                set(
                    self.context[
                        "tags"
                    ]
                )
            )
        )

        if genre:
            return True

        if mood:
            return True

        if detected_strong_tags:
            return True

        if (
            not steam_mode
            and mode
            and platform
        ):
            return True

        return False

    def ask_for_missing_info(
        self,
        steam_mode=False,
    ):
        """
        Formula una única pregunta relevante.
        """

        genre = self.user_preferences[
            "genre"
        ]

        mode = self.user_preferences[
            "mode"
        ]

        mood = self.user_preferences[
            "mood"
        ]

        if (
            mode == "multiplayer"
            and not mood
            and not genre
        ):
            return (
                "¿Qué tipo de experiencia buscas para jugar "
                "con otras personas? Por ejemplo: cooperativa, "
                "competitiva, relajada o difícil."
            )

        if not genre and not mood:
            return (
                "¿Qué tipo de experiencia buscas? "
                "Por ejemplo: RPG, acción, estrategia, terror, "
                "algo relajado, competitivo o difícil."
            )

        if (
            not steam_mode
            and not self.user_preferences[
                "platform"
            ]
        ):
            return (
                "Puedo recomendarte opciones para varias plataformas. "
                "También puedes indicarme una concreta: PC, móvil, "
                "PlayStation, Xbox o Switch."
            )

        return None

    # =========================================================
    # RECOMENDACIÓN GENERAL RAWG
    # =========================================================

    def _recommend_general_from_preferences(
        self,
        clean_text,
        filters=None,
    ):
        """
        Recomienda juegos generales utilizando el motor heurístico.
        """

        if filters is None:
            filters = self._save_preferences(
                clean_text
            )

        filters = dict(
            filters
        )

        # Evitar buscar literalmente frases conversacionales.
        filters["search"] = None

        self._update_context(
            filters
        )

        self.facts.update(
            self.extract_facts(
                clean_text
            )
        )

        self.forward_chaining()

        profile = (
            self._select_inferred_profile()
        )

        request_data = (
            self.recommender.build_request(
                clean_text=clean_text,
                filters=filters,
                context=self.context,
                profile=profile,
            )
        )

        candidates = (
            self.recommender.fetch_candidates(
                request_data=request_data,
                page_size=40,
            )
        )

        games = self.recommender.rank_games(
            games=candidates,
            request_data=request_data,
            limit=5,
        )

        self.context[
            "last_results"
        ] = games

        if not games:
            response = (
                format_no_results_message()
            )

            self._clear_recommendation_preferences()

            return response

        response = format_game_list(
            games,
            request_data,
        )

        self._clear_recommendation_preferences()

        return response

    # =========================================================
    # STEAM
    # =========================================================

    def _extract_steamid(self, text):
        match = re.search(
            r"\b\d{17}\b",
            text,
        )

        return (
            match.group(0)
            if match
            else None
        )

    def _load_steam_library(
        self,
        steamid,
    ):
        """
        Carga y almacena una biblioteca Steam pública.
        """

        library_result = (
            self.steam_library_manager
            .load_library(
                steamid
            )
        )

        if library_result[
            "status"
        ] != "ok":
            self.context[
                "steam_id"
            ] = steamid

            self.context[
                "steam_library_loaded"
            ] = False

            self.context[
                "steam_library"
            ] = []

            self.context[
                "steam_library_map"
            ] = {}

            return library_result[
                "message"
            ]

        games = library_result[
            "games"
        ]

        self.context[
            "steam_id"
        ] = steamid

        self.context[
            "steam_library_loaded"
        ] = True

        self.context[
            "steam_library"
        ] = games

        self.context[
            "steam_library_map"
        ] = (
            self.steam_library_manager
            .build_library_map(
                games
            )
        )

        return (
            self.steam_library_manager
            .format_library_loaded_message(
                steamid,
                library_result[
                    "game_count"
                ],
            )
        )

    def _is_library_query(
        self,
        text,
    ):
        """
        Detecta consultas limitadas a la biblioteca personal.
        """

        library_markers = [
            "mi biblioteca",
            "de mi biblioteca",
            "de steam",
            "mis juegos",
            "mis juegos comprados",
            "que ya tengo",
            "que ya poseo",
            "recomiendame algo que ya tengo",
        ]

        return any(
            marker in text
            for marker in library_markers
        )

    def _recommend_from_steam_library(
        self,
        clean_text,
        filters=None,
    ):
        """
        Recomienda únicamente juegos poseídos por el usuario.
        """

        if not self.context[
            "steam_library_loaded"
        ]:
            return (
                "Primero necesito cargar tu biblioteca de Steam.\n"
                "Pega un SteamID64 con un mensaje como:\n"
                "• cargar steam 7656119XXXXXXXXXX\n\n"
                "Si no puedo leerla, te avisaré de que puede no ser pública."
            )

        self.context[
            "steam_recommendation_mode"
        ] = True

        if filters is None:
            filters = self._save_preferences(
                clean_text
            )

        filters = dict(
            filters
        )

        # Steam define el catálogo.
        # No tiene sentido filtrar por consola.
        filters["search"] = None
        filters["platforms"] = []

        self.context["search"] = None
        self.context["platforms"] = []

        self._update_context(
            filters
        )

        if not self.can_recommend_now(
            steam_mode=True
        ):
            return self.ask_for_missing_info(
                steam_mode=True
            )

        self.facts.update(
            self.extract_facts(
                clean_text
            )
        )

        self.forward_chaining()

        profile = (
            self._select_inferred_profile()
        )

        request_data = (
            self.recommender.build_request(
                clean_text=clean_text,
                filters=filters,
                context=self.context,
                profile=profile,
            )
        )

        request_data[
            "explicit_platforms"
        ] = set()

        candidates = (
            self.recommender.fetch_candidates(
                request_data=request_data,
                page_size=60,
            )
        )

        owned_games = (
            self.steam_library_manager
            .filter_owned_games_from_rawg_results(
                candidates,
                self.context[
                    "steam_library_map"
                ],
            )
        )

        ranked_owned_games = (
            self.recommender.rank_games(
                games=owned_games,
                request_data=request_data,
                limit=5,
            )
        )

        # Compatibilidad primero.
        # Menos horas como desempate.
        ranked_owned_games.sort(
            key=lambda game: (
                game.get(
                    "_recommendation_score",
                    0,
                ),
                -game.get(
                    "steam_playtime_forever",
                    0,
                ),
            ),
            reverse=True,
        )

        self.context[
            "last_results"
        ] = ranked_owned_games

        response = (
            self.steam_library_manager
            .format_library_recommendations(
                ranked_owned_games
            )
        )

        self._clear_recommendation_preferences()

        return response

    def _format_most_played_games(
        self,
        limit=10,
    ):
        """
        Devuelve un ranking de horas jugadas.
        """

        games = sorted(
            self.context[
                "steam_library"
            ],
            key=lambda game: game.get(
                "playtime_forever",
                0,
            ),
            reverse=True,
        )[:limit]

        if not games:
            return (
                "No he encontrado juegos "
                "en tu biblioteca."
            )

        lines = [
            "🎮 Tus juegos más jugados son:\n"
        ]

        for index, game in enumerate(
            games,
            start=1,
        ):
            hours = round(
                game.get(
                    "playtime_forever",
                    0,
                ) / 60,
                1,
            )

            lines.append(
                f"{index}. "
                f"{game.get('name', 'Sin nombre')} "
                f"({hours} horas)"
            )

        return "\n".join(
            lines
        )

    # =========================================================
    # DETALLES Y GUÍAS
    # =========================================================

    def _details_from_index(
        self,
        text,
    ):
        index = (
            self.extractor
            .extract_index_reference(
                text
            )
        )

        if index is None:
            return None

        if not self.context[
            "last_results"
        ]:
            return (
                "No tengo resultados anteriores. "
                "Haz primero una búsqueda."
            )

        result_index = index - 1

        if (
            result_index < 0
            or result_index
            >= len(
                self.context[
                    "last_results"
                ]
            )
        ):
            return (
                "Ese número no corresponde "
                "a ningún juego de la última búsqueda."
            )

        game = self.context[
            "last_results"
        ][result_index]

        details = self.rawg.get_game_details(
            game["slug"]
        )

        self.context[
            "last_game_slug"
        ] = details.get(
            "slug"
        )

        return format_game_details(
            details
        )

    def _details_from_name(
        self,
        text,
    ):
        candidate = (
            self.extractor
            .extract_search_candidate(
                text
            )
        )

        if not candidate:
            return (
                "Dime el nombre del juego "
                "del que quieres saber más."
            )

        candidate_lower = candidate.lower()

        # Buscar primero dentro de las recomendaciones anteriores.
        for game in self.context.get(
            "last_results",
            [],
        ):
            game_name_lower = game.get(
                "name",
                "",
            ).lower()

            if (
                candidate_lower
                in game_name_lower
                or game_name_lower
                in candidate_lower
            ):
                details = self.rawg.get_game_details(
                    game[
                        "slug"
                    ]
                )

                self.context[
                    "last_game_slug"
                ] = details.get(
                    "slug"
                )

                return format_game_details(
                    details
                )

        result = self.rawg.search_games(
            search=candidate,
            page_size=1,
            search_precise=True,
            search_exact=False,
        )

        games = result.get(
            "results",
            [],
        )

        if not games:
            return (
                "No he encontrado ningún juego "
                f"que coincida con '{candidate}'."
            )

        details = self.rawg.get_game_details(
            games[0][
                "slug"
            ]
        )

        self.context[
            "last_game_slug"
        ] = details.get(
            "slug"
        )

        return format_game_details(
            details
        )

    def _format_guide(
        self,
        clean_text,
    ):
        """
        Muestra una guía almacenada en reglas.json.

        Admite:
        - listas de consejos;
        - diccionarios con secciones;
        - textos simples.
        """

        candidate = (
            self.extractor
            .extract_search_candidate(
                clean_text
            )
        )

        if not candidate:
            return (
                "¿De qué juego quieres una guía?"
            )

        candidate = (
            self.extractor
            .preprocess_text(
                candidate
            )
        )

        for guide_key, guide_data in self.guides.items():
            if (
                guide_key in candidate
                or candidate in guide_key
            ):
                title = guide_data[
                    "name"
                ]

                content = guide_data[
                    "content"
                ]

                if isinstance(
                    content,
                    list,
                ):
                    formatted_content = "\n".join(
                        f"• {tip}"
                        for tip in content
                    )

                elif isinstance(
                    content,
                    dict,
                ):
                    sections = []

                    for (
                        section_name,
                        section_content,
                    ) in content.items():
                        sections.append(
                            f"\n{section_name.replace('_', ' ').title()}:"
                        )

                        if isinstance(
                            section_content,
                            list,
                        ):
                            sections.extend(
                                f"• {item}"
                                for item in section_content
                            )

                        else:
                            sections.append(
                                str(
                                    section_content
                                )
                            )

                    formatted_content = "\n".join(
                        sections
                    )

                else:
                    formatted_content = str(
                        content
                    )

                return (
                    f"🎮 Guía básica de {title}:\n\n"
                    f"{formatted_content}"
                )

        return (
            "No tengo una guía almacenada "
            f"para '{candidate}'."
        )

    # =========================================================
    # TOP JUEGOS PARA MÓVIL
    # =========================================================

    def _format_top_mobile_games(self):
        """
        Devuelve un ranking sencillo para móvil.
        """

        result = self.rawg.search_games(
            platforms="21",
            ordering="-added",
            page_size=5,
        )

        games = result.get(
            "results",
            [],
        )

        self.context[
            "last_results"
        ] = games

        safe_context = {
            "genres": [],
            "tags": [],
            "platforms": [21],
            "ordering": "-added",
        }

        return format_game_list(
            games,
            safe_context,
        )

    # =========================================================
    # RESPUESTA PRINCIPAL
    # =========================================================

    def respond(
        self,
        user_input,
    ):
        """
        Procesa un mensaje y devuelve una respuesta.
        """

        try:
            clean_text = (
                self.extractor
                .preprocess_text(
                    user_input
                )
            )

            intent = detect_intent(
                clean_text
            )

            steamid = self._extract_steamid(
                clean_text
            )

            # =================================================
            # 1. CARGAR STEAM Y EJECUTAR ACCIONES COMPUESTAS
            # =================================================

            if (
                steamid
                and "steam" in clean_text
            ):
                load_message = (
                    self._load_steam_library(
                        steamid
                    )
                )

                if not self.context[
                    "steam_library_loaded"
                ]:
                    return load_message

                if intent == "most_played":
                    return (
                        f"{load_message}\n\n"
                        f"{self._format_most_played_games()}"
                    )

                if self._is_library_query(
                    clean_text
                ):
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

            # SteamID inválido.
            steam_commands = [
                "cargar steam",
                "carga steam",
                "conectar steam",
                "steamid",
            ]

            if (
                self._contains_any_phrase(
                    clean_text,
                    steam_commands,
                )
                and not steamid
            ):
                return (
                    "No he encontrado un SteamID64 válido "
                    "en tu mensaje.\n"
                    "Usa algo como:\n"
                    "• cargar steam 7656119XXXXXXXXXX"
                )

            # =================================================
            # 2. INTENCIONES GENERALES
            # =================================================

            if intent == "greeting":
                return format_welcome_message()

            if intent == "farewell":
                return format_goodbye_message()

            if intent == "reset":
                self.reset()

                return format_reset_message()

            if intent == "genres":
                return format_genres_list(
                    self.rawg.get_genres(
                        page_size=50
                    )
                )

            if intent == "platforms":
                return format_platforms_list(
                    self.rawg.get_platforms(
                        page_size=50
                    )
                )

            if intent == "help":
                return format_help_message()

            if intent == "guide":
                return self._format_guide(
                    clean_text
                )

            # =================================================
            # 3. ESTADÍSTICAS STEAM
            # =================================================

            if intent == "most_played":
                if not self.context[
                    "steam_library_loaded"
                ]:
                    return (
                        "Primero debes cargar tu biblioteca de Steam.\n"
                        "Ejemplo:\n"
                        "• cargar steam 7656119XXXXXXXXXX"
                    )

                return self._format_most_played_games()

            # =================================================
            # 4. DETALLES
            # =================================================

            if intent == "details":
                result = self._details_from_index(
                    clean_text
                )

                if result:
                    return result

                return self._details_from_name(
                    clean_text
                )

            # =================================================
            # 5. TOP MÓVIL
            # =================================================

            if intent == "top_games":
                return self._format_top_mobile_games()

            # =================================================
            # 6. BIBLIOTECA STEAM
            # =================================================

            if self._is_library_query(
                clean_text
            ):
                self._clear_recommendation_preferences()

                return self._recommend_from_steam_library(
                    clean_text
                )

            if self.context[
                "steam_recommendation_mode"
            ]:
                return self._recommend_from_steam_library(
                    clean_text
                )

            # =================================================
            # 7. RECOMENDACIÓN GENERAL RAWG
            # =================================================

            filters = self._save_preferences(
                clean_text
            )

            if self.can_recommend_now(
                steam_mode=False
            ):
                return (
                    self._recommend_general_from_preferences(
                        clean_text,
                        filters=filters,
                    )
                )

            has_any_preference = any([
                self.user_preferences[
                    "platform"
                ],
                self.user_preferences[
                    "mode"
                ],
                self.user_preferences[
                    "mood"
                ],
                self.user_preferences[
                    "genre"
                ],
                self.context[
                    "tags"
                ],
                self.context[
                    "genres"
                ],
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

        except Exception as error:
            return format_error_message(
                str(error)
            )