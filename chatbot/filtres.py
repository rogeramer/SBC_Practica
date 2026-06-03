import re
import unicodedata


class FilterExtractor:
    def __init__(self, rawg_service):
        self.rawg = rawg_service

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

        self.tag_aliases = {
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

            "cooperativo": "co-op",
            "cooperativa": "co-op",
            "cooperatiu": "co-op",
            "coop": "co-op",
            "co-op": "co-op",

            "multijugador": "multiplayer",
            "multiplayer": "multiplayer",

            "singleplayer": "singleplayer",
            "single player": "singleplayer",
            "solitario": "singleplayer",
            "solitari": "singleplayer",
            "solo": "singleplayer",

            "historia rica": "story-rich",
            "buena historia": "story-rich",
            "narrativo": "story-rich",
            "narrativa": "story-rich",
            "historia": "story-rich",

            "mundo abierto": "open-world",
            "open world": "open-world",

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


    def preprocess_text(self, text):
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


    def references_last_result(self, text):
        last_result_markers = [
            "ultimo",
            "ultima",
            "el ultimo",
            "la ultima",
            "ultimo juego",
            "ultima recomendacion",
            "el ultimo juego",
            "el ultimo recomendado",
            "el ultimo que has recomendado",
            "el ultimo que me has recomendado",
        ]

        return any(
            marker in text
            for marker in last_result_markers
        )

    def extract_index_reference(
        self,
        text,
    ):
        match = re.search(
            r"\b(\d+)\b",
            text,
        )
        if not match:
            return None
        return int(
            match.group(1)
        )

    def references_last_result(self, text):
        last_result_markers = [
            "ultimo",
            "ultima",
            "el ultimo",
            "la ultima",
            "ultimo juego",
            "ultima recomendacion",
            "el ultimo juego",
            "el ultimo recomendado",
            "el ultimo que has recomendado",
            "el ultimo que me has recomendado",
        ]
        return any(
            marker in text
            for marker in last_result_markers
        )

    def references_last_result(self, text):
        last_result_markers = [
            "ultimo",
            "ultima",
            "el ultimo",
            "la ultima",
            "ultimo juego",
            "ultima recomendacion",
            "el ultimo juego",
            "el ultimo recomendado",
            "el ultimo que has recomendado",
            "el ultimo que me has recomendado",
        ]
        return any(
            marker in text
            for marker in last_result_markers
        )

    def extract_search_candidate(self, text):
        candidate = self.preprocess_text(
            text
        )
        cleanup_patterns = [
            r"^quiero que me expliques de que trata\s+",
            r"^quiero que me expliques\s+",
            r"^quiero saber de que trata\s+",
            r"^explicame de que trata\s+",
            r"^explica de que trata\s+",
            r"^dime de que trata\s+",
            r"^de que trata\s+",

            r"^dame una guia de\s+",
            r"^dame una guia del\s+",
            r"^quiero una guia de\s+",
            r"^quiero una guia del\s+",
            r"^guia de\s+",
            r"^guia del\s+",

            r"^quiero informacion de\s+",
            r"^quiero informacion del\s+",
            r"^informacion de\s+",
            r"^informacion del\s+",
            r"^info de\s+",
            r"^info del\s+",

            r"^quiero detalles de\s+",
            r"^quiero detalles del\s+",
            r"^detalles de\s+",
            r"^detalles del\s+",
            r"^detalle de\s+",
            r"^detalle del\s+",

            r"^explicame\s+",
            r"^explica\s+",
            r"^dime\s+",
            r"^muestrame\s+",
        ]
        changed = True
        while changed:
            previous_candidate = candidate
            for pattern in cleanup_patterns:
                candidate = re.sub(
                    pattern,
                    "",
                    candidate,
                ).strip()
            changed = (
                    previous_candidate
                    != candidate
            )
        candidate = re.sub(
            r"\s+",
            " ",
            candidate,
        ).strip()
        if len(candidate) < 2:
            return None
        return candidate

    def extract_filters(self, text):
        text = self.preprocess_text(
            text
        )
        genres = []
        tags = []
        platforms = []
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

    def _infer_search_text(
        self,
        text,
        genres,
        tags,
        platforms,
    ):
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