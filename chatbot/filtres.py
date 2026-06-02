import re
import unicodedata


class FilterExtractor:
    """
    Extrae filtros RAWG a partir del texto escrito por el usuario.

    Responsabilidades:
    - normalizar el texto;
    - detectar géneros;
    - detectar etiquetas;
    - detectar plataformas;
    - detectar ordenación;
    - detectar años y rangos de Metacritic;
    - inferir búsquedas por nombre cuando no hay filtros explícitos.
    """

    def __init__(self, rawg_service):
        self.rawg = rawg_service

        # Catálogos reales obtenidos desde RAWG.
        self.genres_catalog = self.rawg.get_genres(
            page_size=50
        )

        self.tags_catalog = self.rawg.get_tags(
            page_size=100
        )

        self.platforms_catalog = self.rawg.get_platforms(
            page_size=100
        )

        self.genre_lookup = self._build_lookup(
            self.genres_catalog
        )

        self.tag_lookup = self._build_lookup(
            self.tags_catalog
        )

        self.platform_lookup = (
            self._build_platform_lookup(
                self.platforms_catalog
            )
        )

        # =====================================================
        # ORDENACIÓN
        # =====================================================

        self.order_keywords = {
            "mejor valorados": "-rating",
            "mejor valorado": "-rating",
            "mejores valorados": "-rating",
            "rating": "-rating",
            "puntuacion": "-rating",
            "metacritic": "-metacritic",

            "populares": "-added",
            "popular": "-added",
            "mas populares": "-added",

            "nuevos": "-released",
            "recientes": "-released",
            "proximos": "-released",
            "futuros": "-released",

            "antiguos": "released",
        }

        # =====================================================
        # PLATAFORMAS
        # =====================================================
        #
        # El texto llega normalizado:
        # "móvil" → "movil"
        # =====================================================

        self.platform_aliases = {
            "nintendo switch": 7,
            "switch": 7,

            "xbox series x": 186,
            "xbox series s": 186,
            "xbox one": 1,
            "xbox": 1,

            "playstation 5": 187,
            "playstation": 187,
            "ps5": 187,
            "ps4": 18,

            "android": 21,
            "mobile": 21,
            "mobil": 21,
            "movil": 21,

            "ios": 3,
            "iphone": 3,
            "ipad": 3,

            "windows": 4,
            "pc": 4,

            "macos": 5,
            "mac": 5,

            "linux": 6,
        }

        # =====================================================
        # TAGS
        # =====================================================
        #
        # Los alias específicos aparecen antes que los generales.
        # El código también los ordenará por longitud para evitar
        # perder precisión.
        # =====================================================

        self.tag_aliases = {
            # Cooperativo específico
            "cooperativo online": "online-co-op",
            "cooperativa online": "online-co-op",
            "cooperatiu online": "online-co-op",
            "coop online": "online-co-op",

            "cooperativo local": "local-co-op",
            "cooperativa local": "local-co-op",
            "cooperatiu local": "local-co-op",
            "coop local": "local-co-op",

            "pantalla dividida": "split-screen",
            "split screen": "split-screen",

            # Cooperativo genérico
            "cooperativo": "co-op",
            "cooperativa": "co-op",
            "cooperatiu": "co-op",
            "coop": "co-op",
            "co-op": "co-op",

            # Multijugador
            "multijugador": "multiplayer",
            "multiplayer": "multiplayer",

            # Solitario
            "singleplayer": "singleplayer",
            "single player": "singleplayer",
            "solitario": "singleplayer",
            "solitari": "singleplayer",
            "solo": "singleplayer",

            # Narrativa
            "historia rica": "story-rich",
            "buena historia": "story-rich",
            "narrativo": "story-rich",
            "narrativa": "story-rich",
            "historia": "story-rich",

            # Exploración
            "mundo abierto": "open-world",
            "open world": "open-world",

            # Estilo
            "relajante": "relaxing",
            "relajado": "relaxing",
            "relajada": "relaxing",
            "tranquilo": "relaxing",
            "tranquila": "relaxing",
            "chill": "relaxing",

            "competitivo": "competitive",
            "competitiva": "competitive",
            "competitive": "competitive",
            "ranked": "competitive",

            "dificil": "difficult",
            "reto": "difficult",
            "desafio": "difficult",
            "hard": "difficult",

            # Temáticas y mecánicas
            "terror": "horror",
            "miedo": "horror",
            "horror": "horror",

            "pixel art": "pixel-graphics",
            "roguelike": "roguelike",
            "roguelite": "roguelite",
            "soulslike": "souls-like",
            "souls-like": "souls-like",
            "zombies": "zombies",
            "survival": "survival",
            "sandbox": "sandbox",
            "por turnos": "turn-based",
            "turn based": "turn-based",
        }

        # =====================================================
        # GÉNEROS
        # =====================================================

        self.genre_aliases = {
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
            "puzle": "puzzle",
            "puzles": "puzzle",

            "deportes": "sports",
            "sports": "sports",

            "carreras": "racing",
            "racing": "racing",

            "shooter": "shooter",

            "lucha": "fighting",
            "fighting": "fighting",

            "plataformas": "platformer",
            "platformer": "platformer",

            "arcade": "arcade",
            "indie": "indie",
            "casual": "casual",
        }

    # =========================================================
    # NORMALIZACIÓN
    # =========================================================

    def preprocess_text(self, text):
        """
        Normaliza el texto del usuario.

        Ejemplos:
        - "Móvil" → "movil"
        - "Acción" → "accion"
        - "Co-op" → "co-op"
        """

        text = str(text or "").lower()

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        text = text.encode(
            "ascii",
            "ignore",
        ).decode(
            "ascii"
        )

        # Mantener guiones porque RAWG utiliza slugs como:
        # co-op, open-world, story-rich...
        text = re.sub(
            r"[^\w\s\-]",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    def _contains_phrase(self, text, phrase):
        """
        Comprueba si una palabra o expresión aparece completa.

        Evita falsos positivos como:
        - "pc" dentro de otra palabra;
        - "ios" dentro de "curiosos".
        """

        pattern = (
            rf"(?<!\w)"
            rf"{re.escape(phrase)}"
            rf"(?!\w)"
        )

        return bool(
            re.search(
                pattern,
                text,
            )
        )

    # =========================================================
    # CATÁLOGOS RAWG
    # =========================================================

    def _build_lookup(self, items):
        lookup = {}

        for item in items:
            slug = self.preprocess_text(
                item.get("slug", "")
            )

            name = self.preprocess_text(
                item.get("name", "")
            )

            if slug:
                lookup[slug] = item

            if name:
                lookup[name] = item

        return lookup

    def _build_platform_lookup(self, items):
        lookup = {}

        for item in items:
            platform_id = item.get("id")

            name = self.preprocess_text(
                item.get("name", "")
            )

            slug = self.preprocess_text(
                item.get("slug", "")
            )

            if platform_id is not None:
                lookup[str(platform_id)] = item

            if name:
                lookup[name] = item

            if slug:
                lookup[slug] = item

        return lookup

    # =========================================================
    # REFERENCIAS A RESULTADOS ANTERIORES
    # =========================================================

    def extract_index_reference(self, text):
        """
        Extrae referencias como:
        - detalles del 1
        - información del 3
        """

        match = re.search(
            r"\b(\d+)\b",
            text,
        )

        if match:
            return int(
                match.group(1)
            )

        return None

    def extract_search_candidate(self, text):
        cleanup_patterns = [
            r"\bdetalles?\b",
            r"\bdetalle\b",
            r"\binfo\b",
            r"\binformacion\b",
            r"\bficha\b",

            r"\bguia\b",
            r"\bconsejos?\b",
            r"\btips?\b",

            r"\bdame\b",
            r"\bquiero\b",
            r"\bexplicame\b",
            r"\bexplica\b",
            r"\bde que trata\b",
            r"\bcomo empezar\b",
            r"\bayudame a empezar\b",

            r"\bdel\b",
            r"\bde\b",
            r"\bpara\b",
            r"\bel\b",
            r"\bla\b",
            r"\bun\b",
            r"\buna\b",
            r"\bjuego\b",
            r"\bgame\b",
        ]

        candidate = text

        for pattern in cleanup_patterns:
            candidate = re.sub(
                pattern,
                " ",
                candidate,
            )

        candidate = re.sub(
            r"\s+",
            " ",
            candidate,
        ).strip()

        if len(
                candidate
        ) < 2:
            return None

        return candidate

    # =========================================================
    # EXTRACCIÓN DE FILTROS
    # =========================================================

    def extract_filters(self, text):
        """
        Devuelve un diccionario compatible con RAWG:

        {
            "search": None | str,
            "genres": [...],
            "tags": [...],
            "platforms": [...],
            "ordering": None | str,
            "dates": None | str,
            "metacritic": None | str,
        }
        """

        text = self.preprocess_text(
            text
        )

        genres = []
        tags = []
        platforms = []

        # Catálogo real de RAWG.
        for key, item in self.genre_lookup.items():
            if (
                key
                and self._contains_phrase(
                    text,
                    key,
                )
            ):
                slug = item.get("slug")

                if slug and slug not in genres:
                    genres.append(slug)

        # Alias conversacionales.
        for alias, slug in sorted(
            self.genre_aliases.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if (
                self._contains_phrase(
                    text,
                    alias,
                )
                and slug not in genres
            ):
                genres.append(slug)

        # Catálogo real de tags RAWG.
        for key, item in self.tag_lookup.items():
            if (
                key
                and self._contains_phrase(
                    text,
                    key,
                )
            ):
                slug = item.get("slug")

                if slug and slug not in tags:
                    tags.append(slug)

        # Alias de tags.
        for alias, slug in sorted(
            self.tag_aliases.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if (
                self._contains_phrase(
                    text,
                    alias,
                )
                and slug not in tags
            ):
                tags.append(slug)

        # Plataformas.
        for alias, platform_id in sorted(
            self.platform_aliases.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if (
                self._contains_phrase(
                    text,
                    alias,
                )
                and platform_id not in platforms
            ):
                platforms.append(
                    platform_id
                )

        # Ordenación.
        ordering = None

        for key, value in sorted(
            self.order_keywords.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if self._contains_phrase(
                text,
                key,
            ):
                ordering = value
                break

        # Detectar cualquier año razonable:
        # 2022, 2025, 2026, 2030...
        dates = None

        year_match = re.search(
            r"\b(20\d{2})\b",
            text,
        )

        if year_match:
            year = year_match.group(1)

            dates = (
                f"{year}-01-01,"
                f"{year}-12-31"
            )

        # Metacritic.
        metacritic = None

        if re.search(
            r"\bmetacritic\s+"
            r"(alto|alta|bueno|buena)\b",
            text,
        ):
            metacritic = "80,100"

        search = self._infer_search_text(
            text,
            genres,
            tags,
            platforms,
        )

        return {
            "search": search,
            "genres": genres,
            "tags": tags,
            "platforms": platforms,
            "ordering": ordering,
            "dates": dates,
            "metacritic": metacritic,
        }

    # =========================================================
    # BÚSQUEDA POR NOMBRE
    # =========================================================

    def _infer_search_text(
        self,
        text,
        genres,
        tags,
        platforms,
    ):
        """
        Si no hay filtros explícitos, intenta interpretar
        el texto restante como el nombre de un juego.
        """

        generic_words = {
            "quiero",
            "busco",
            "juego",
            "juegos",
            "de",
            "del",
            "con",
            "para",
            "por",
            "y",
            "un",
            "una",
            "unos",
            "unas",
            "dame",
            "algo",
            "top",
            "mejores",
            "recomienda",
            "recomiendame",

            "pc",
            "windows",
            "switch",
            "xbox",
            "playstation",
            "ps4",
            "ps5",
            "ios",
            "android",
            "mobile",
            "mobil",
            "movil",
            "linux",
            "mac",

            "popular",
            "populares",
            "rating",
            "metacritic",
            "recientes",
            "nuevos",
            "proximos",
            "proximamente",
            "futuros",
            "upcoming",
        }

        tokens = [
            token
            for token in text.split()
            if token not in generic_words
        ]

        # Si ya existen filtros, no buscamos literalmente
        # una frase conversacional dentro del nombre.
        if genres or tags or platforms:
            return None

        if not tokens:
            return None

        candidate = " ".join(
            tokens[:8]
        ).strip()

        if len(candidate) < 2:
            return None

        return candidate