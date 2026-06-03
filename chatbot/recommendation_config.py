PLATFORM_MAP = {
    "pc": 4,
    "playstation": 187,
    "ps5": 187,
    "ps4": 18,
    "xbox": 1,
    "xbox one": 1,
    "xbox series": 186,
    "xbox series x": 186,
    "xbox series s": 186,
    "switch": 7,
    "nintendo switch": 7,
    "ios": 3,
    "android": 21,
    "movil": 21,
    "móvil": 21,
    "mac": 5,
    "linux": 6,
}

PLATFORM_LABELS = {
    4: "PC",
    187: "PlayStation 5",
    18: "PlayStation 4",
    1: "Xbox One",
    186: "Xbox Series S/X",
    7: "Nintendo Switch",
    3: "iOS",
    21: "Android",
    5: "macOS",
    6: "Linux",
}



COOP_TAGS = {
    "co-op",
    "online-co-op",
    "local-co-op",
    "couch-co-op",
    "split-screen",
}

LOCAL_COOP_TAGS = {
    "local-co-op",
    "couch-co-op",
    "split-screen",
}

MULTIPLAYER_TAGS = {
    "multiplayer",
    "online-co-op",
    "local-co-op",
    "co-op",
    "massively-multiplayer",
}

HORROR_TAGS = {
    "horror",
    "survival-horror",
}


GENRE_LABELS = {
    "role-playing-games-rpg": "RPG",
    "action": "acción",
    "adventure": "aventura",
    "strategy": "estrategia",
    "simulation": "simulación",
    "puzzle": "puzles",
    "sports": "deportes",
    "racing": "carreras",
    "shooter": "shooter",
    "fighting": "lucha",
    "platformer": "plataformas",
    "indie": "indie",
    "casual": "casual",
}


TAG_REASON_LABELS = {
    "story-rich": "tiene una historia destacada",
    "relaxing": "ofrece una experiencia relajada",
    "competitive": "está orientado a partidas competitivas",
    "multiplayer": "permite jugar con otras personas",
    "co-op": "incluye un modo cooperativo",
    "online-co-op": "permite cooperativo online",
    "local-co-op": "permite cooperativo local",
    "couch-co-op": "permite cooperativo local",
    "split-screen": "permite jugar a pantalla dividida",
    "shared-split-screen": "permite jugar a pantalla dividida",
    "shared-split-screen-co-op": "permite cooperativo a pantalla dividida",
    "singleplayer": "se puede disfrutar en solitario",
    "horror": "encaja con una experiencia de terror",
    "survival-horror": "encaja con una experiencia de terror",
    "difficult": "ofrece un reto elevado",
    "open-world": "permite explorar un mundo abierto",
    "souls-like": "tiene características souls-like",
    "fast-paced": "propone partidas de ritmo rápido",
}


STRICT_TAGS = {
    "story-rich",
    "horror",
    "relaxing",
    "competitive",
    "difficult",
    "open-world",
    "singleplayer",
}


COOP_SUPPORT_TAGS = {
    "online-co-op",
    "local-co-op",
    "couch-co-op",
    "split-screen",
    "shared-split-screen",
    "shared-split-screen-co-op",
    "local-multiplayer",
}


ONLY_UNRELEASED_MARKERS = {
    "proximo",
    "proximos",
    "proximamente",
    "futuro",
    "futuros",
    "por salir",
    "upcoming",
}

ALLOW_UNRELEASED_MARKERS = {
    "incluyendo proximos",
    "incluye proximos",
    "tambien proximos",
    "tambien futuros",
    "publicados y futuros",
}


PROFILE_TO_RAWG = {
    "perfil_chill_solitario": {
        "genres": ["indie", "casual"],
        "tags": ["singleplayer", "relaxing"],
    },
    "perfil_narrativo": {
        "genres": ["adventure", "role-playing-games-rpg"],
        "tags": ["story-rich", "singleplayer"],
    },
    "perfil_competitivo_online": {
        "genres": ["action", "shooter"],
        "tags": ["multiplayer", "competitive"],
    },
    "perfil_coop_relajado": {
        "genres": ["indie", "casual"],
        "tags": ["co-op", "multiplayer", "relaxing"],
    },
    "perfil_terror_grupo": {
        "genres": ["action", "indie"],
        "tags": ["horror", "co-op", "multiplayer"],
    },
    "perfil_estrategia_corta": {
        "genres": ["strategy"],
        "tags": ["turn-based", "fast-paced"],
    },
    "perfil_accion_dificil": {
        "genres": ["action"],
        "tags": ["difficult", "souls-like"],
    },
    "perfil_exploracion_solo": {
        "genres": ["adventure"],
        "tags": ["open-world", "singleplayer"],
    },
    "perfil_terror_solo": {
        "genres": ["action", "adventure"],
        "tags": ["horror", "singleplayer"],
    },
    "perfil_accion_rapida": {
        "genres": ["action", "indie"],
        "tags": ["fast-paced", "roguelike"],
    },
    "perfil_exploracion_coop": {
        "genres": ["adventure"],
        "tags": ["open-world", "co-op"],
    },
    "perfil_shooter_coop": {
        "genres": ["shooter"],
        "tags": ["co-op"],
    },
    "perfil_coop_historia": {
        "genres": ["adventure", "role-playing-games-rpg"],
        "tags": ["co-op", "story-rich"],
    },
    "perfil_estrategia_multi": {
        "genres": ["strategy"],
        "tags": ["multiplayer"],
    },
    "perfil_terror_rapido": {
        "genres": ["action"],
        "tags": ["horror", "fast-paced"],
    },
    "perfil_accion_multi_rapido": {
        "genres": ["action"],
        "tags": ["multiplayer", "fast-paced"],
    },
    "perfil_estrategia_chill": {
        "genres": ["strategy", "casual"],
        "tags": ["relaxing", "singleplayer"],
    },
    "perfil_estrategia_multi_rapida": {
        "genres": ["strategy"],
        "tags": ["multiplayer", "fast-paced"],
    },
    "perfil_estrategia_multi_larga": {
        "genres": ["strategy"],
        "tags": ["multiplayer", "turn-based"],
    },
    "perfil_accion_chill_multi": {
        "genres": ["action", "casual"],
        "tags": ["multiplayer", "relaxing"],
    },
}


PROFILE_PRIORITY = {
    "perfil_shooter_coop": 100,
    "perfil_coop_historia": 95,
    "perfil_exploracion_coop": 90,
    "perfil_estrategia_multi_rapida": 88,
    "perfil_estrategia_multi_larga": 87,
    "perfil_accion_multi_rapido": 85,
    "perfil_accion_chill_multi": 84,
    "perfil_terror_grupo": 82,
    "perfil_terror_solo": 81,
    "perfil_accion_dificil": 80,
    "perfil_competitivo_online": 78,
    "perfil_coop_relajado": 76,
    "perfil_exploracion_solo": 74,
    "perfil_narrativo": 72,
    "perfil_chill_solitario": 70,
    "perfil_estrategia_multi": 68,
    "perfil_estrategia_chill": 66,
    "perfil_estrategia_corta": 64,
    "perfil_terror_rapido": 62,
    "perfil_accion_rapida": 60,
}