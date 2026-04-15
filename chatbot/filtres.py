import re


class Filtres:
    def __init__(self, rawg_service):
        self.rawg = rawg_service

        self.genres_catalog = self.rawg.get_genres(page_size=50)
        self.tags_catalog = self.rawg.get_tags(page_size=100)
        self.platforms_catalog = self.rawg.get_platforms(page_size=100)

        self.genre_lookup = self._build_lookup(self.genres_catalog)
        self.tag_lookup = self._build_lookup(self.tags_catalog)
        self.platform_lookup = self._build_platform_lookup(self.platforms_catalog)

        self.order_keywords = {
            "mejor valorados": "-rating",
            "mejor valorado": "-rating",
            "rating": "-rating",
            "puntuacion": "-rating",
            "puntuación": "-rating",
            "metacritic": "-metacritic",
            "populares": "-added",
            "popular": "-added",
            "nuevos": "-released",
            "recientes": "-released",
            "antiguos": "released",
        }

        self.platform_aliases = {
            "pc": 4,
            "playstation": 187,
            "ps5": 187,
            "ps4": 18,
            "xbox": 1,
            "xbox one": 1,
            "xbox series x": 186,
            "xbox series s": 186,
            "switch": 7,
            "nintendo switch": 7,
            "ios": 3,
            "android": 21,
            "mac": 5,
            "linux": 6,
        }

        self.tag_aliases = {
            "mundo abierto": "open-world",
            "coop": "co-op",
            "cooperativo": "co-op",
            "multijugador": "multiplayer",
            "singleplayer": "singleplayer",
            "solo": "singleplayer",
            "terror": "horror",
            "por": "horror",
            "historia": "story-rich",
            "historia rica": "story-rich",
            "relajante": "relaxing",
            "relajado": "relaxing",
            "dificil": "difficult",
            "difícil": "difficult",
            "indie": "indie",
            "pixel art": "pixel-graphics",
            "roguelike": "roguelike",
            "roguelite": "roguelite",
            "soulslike": "souls-like",
            "zombies": "zombies",
            "survival": "survival",
            "sandbox": "sandbox",
        }

    def preprocess_text(self, text):
        text = text.lower()
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
            "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
            "ü": "u", "ï": "i", "ç": "c"
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"[^\w\s\-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _build_lookup(self, items):
        lookup = {}
        for item in items:
            slug = item.get("slug", "").lower()
            name = item.get("name", "").lower()

            if slug:
                lookup[slug] = item
            if name:
                lookup[name] = item
        return lookup

    def _build_platform_lookup(self, items):
        lookup = {}
        for item in items:
            pid = item.get("id")
            name = item.get("name", "").lower()
            slug = item.get("slug", "").lower()

            if pid is not None:
                lookup[str(pid)] = item
            if name:
                lookup[name] = item
            if slug:
                lookup[slug] = item
        return lookup

    def extract_index_reference(self, text):
        match = re.search(r"\b(\d+)\b", text)
        if match:
            return int(match.group(1))
        return None

    def extract_search_candidate(self, text):
        cleanup_patterns = [
            r"\bdetalles?\b",
            r"\binfo\b",
            r"\binformacion\b",
            r"\binformación\b",
            r"\bficha\b",
            r"\bdel\b",
            r"\bde\b",
            r"\bel\b",
            r"\bla\b",
            r"\bgame\b",
            r"\bjuego\b",
        ]

        candidate = text
        for pattern in cleanup_patterns:
            candidate = re.sub(pattern, " ", candidate)

        candidate = re.sub(r"\s+", " ", candidate).strip()

        if len(candidate) < 2:
            return None
        return candidate

    def extract_filters(self, text):
        genres = []
        tags = []
        platforms = []

        for key, item in self.genre_lookup.items():
            if key and re.search(rf"\b{re.escape(key)}\b", text):
                slug = item["slug"]
                if slug not in genres:
                    genres.append(slug)

        for key, item in self.tag_lookup.items():
            if key and re.search(rf"\b{re.escape(key)}\b", text):
                slug = item["slug"]
                if slug not in tags:
                    tags.append(slug)

        for alias, slug in self.tag_aliases.items():
            if alias in text and slug not in tags:
                tags.append(slug)

        for alias, platform_id in self.platform_aliases.items():
            if alias in text and platform_id not in platforms:
                platforms.append(platform_id)

        ordering = None
        for key, value in self.order_keywords.items():
            if key in text:
                ordering = value
                break

        dates = None
        if "2025" in text:
            dates = "2025-01-01,2025-12-31"
        elif "2024" in text:
            dates = "2024-01-01,2024-12-31"
        elif "2023" in text:
            dates = "2023-01-01,2023-12-31"
        elif "2022" in text:
            dates = "2022-01-01,2022-12-31"

        metacritic = None
        if "metacritic alto" in text or "metacritic buena" in text or "metacritic bueno" in text:
            metacritic = "80,100"

        search = self._infer_search_text(text, genres, tags, platforms)

        return {
            "search": search,
            "genres": genres,
            "tags": tags,
            "platforms": platforms,
            "ordering": ordering,
            "dates": dates,
            "metacritic": metacritic,
        }

    def _infer_search_text(self, text, genres, tags, platforms):
        generic_words = {
            "quiero", "busco", "juego", "juegos", "de", "del", "con", "para", "y",
            "un", "una", "unos", "unas", "dame", "algo", "top", "mejores",
            "pc", "switch", "xbox", "playstation", "ps4", "ps5", "ios", "android",
            "popular", "populares", "rating", "metacritic", "recientes", "nuevos",
        }

        tokens = [t for t in text.split() if t not in generic_words]

        if genres or tags or platforms:
            return None

        if not tokens:
            return None

        candidate = " ".join(tokens[:8]).strip()
        if len(candidate) < 2:
            return None
        return candidate