"""
Configuración estática del recomendador.

Este módulo contiene:
- traducción de perfiles inferidos a filtros RAWG;
- prioridades para resolver conflictos entre reglas;
- alias y etiquetas legibles;
- señales utilizadas por el ranking heurístico.

No contiene lógica de ejecución.
La lógica se implementa en recommendation_engine.py.
"""


# =========================================================
# PERFILES DEL SISTEMA EXPERTO
# =========================================================

PROFILE_TO_RAWG = {
    "perfil_chill_solitario": {
        "genres": "indie,casual",
        "tags": "singleplayer,relaxing",
    },
    "perfil_narrativo": {
        "genres": "adventure,role-playing-games-rpg",
        "tags": "story-rich,singleplayer",
    },
    "perfil_competitivo_online": {
        "genres": "action,shooter",
        "tags": "multiplayer,competitive",
    },
    "perfil_coop_relajado": {
        "genres": "indie,casual",
        "tags": "co-op,multiplayer,relaxing",
    },
    "perfil_terror_grupo": {
        "genres": "action,indie",
        "tags": "horror,co-op,multiplayer",
    },
    "perfil_estrategia_corta": {
        "genres": "strategy",
        "tags": "turn-based",
    },
    "perfil_accion_dificil": {
        "genres": "action",
        "tags": "difficult,souls-like",
    },
    "perfil_exploracion_solo": {
        "genres": "adventure",
        "tags": "open-world,singleplayer",
    },
    "perfil_terror_solo": {
        "genres": "action,adventure",
        "tags": "horror,singleplayer",
    },
    "perfil_accion_rapida": {
        "genres": "action,indie",
        "tags": "fast-paced,roguelike",
    },
    "perfil_exploracion_coop": {
        "genres": "adventure",
        "tags": "open-world,co-op",
    },
    "perfil_shooter_coop": {
        "genres": "shooter",
        "tags": "co-op",
    },
    "perfil_coop_historia": {
        "genres": "adventure,role-playing-games-rpg",
        "tags": "co-op,story-rich",
    },
    "perfil_estrategia_multi": {
        "genres": "strategy",
        "tags": "multiplayer",
    },
    "perfil_terror_rapido": {
        "genres": "action",
        "tags": "horror,fast-paced",
    },
    "perfil_accion_multi_rapido": {
        "genres": "action",
        "tags": "multiplayer,fast-paced",
    },
    "perfil_estrategia_chill": {
        "genres": "strategy,casual",
        "tags": "relaxing,singleplayer",
    },
    "perfil_estrategia_multi_rapida": {
        "genres": "strategy",
        "tags": "multiplayer,fast-paced",
    },
    "perfil_estrategia_multi_larga": {
        "genres": "strategy",
        "tags": "multiplayer,turn-based",
    },
    "perfil_accion_chill_multi": {
        "genres": "action,casual",
        "tags": "multiplayer,relaxing",
    },
}


# =========================================================
# PRIORIDADES PARA RESOLUCIÓN DE CONFLICTOS
# =========================================================
#
# Cuando varias reglas deducen perfiles distintos:
# 1. recommendation_engine / main compara especificidad;
# 2. en caso de empate, utiliza estas prioridades.
#
# Cuanto mayor sea el número, mayor prioridad.
# =========================================================

PROFILE_PRIORITY = {
    "perfil_competitivo_online": 100,
    "perfil_terror_grupo": 95,
    "perfil_coop_historia": 90,
    "perfil_shooter_coop": 90,
    "perfil_exploracion_coop": 85,
    "perfil_estrategia_multi_rapida": 85,
    "perfil_estrategia_multi_larga": 85,
    "perfil_accion_multi_rapido": 80,
    "perfil_coop_relajado": 80,
    "perfil_accion_dificil": 75,
    "perfil_terror_solo": 75,
    "perfil_terror_rapido": 75,
    "perfil_narrativo": 70,
    "perfil_exploracion_solo": 70,
    "perfil_accion_rapida": 65,
    "perfil_estrategia_corta": 65,
    "perfil_estrategia_chill": 65,
    "perfil_accion_chill_multi": 60,
    "perfil_chill_solitario": 50,
}


# =========================================================
# PLATAFORMAS
# =========================================================
#
# Los textos llegan normalmente preprocesados y sin acentos:
# "móvil" → "movil"
# =========================================================

PLATFORM_MAP = {
    "android": 21,
    "mobile": 21,
    "mobil": 21,
    "movil": 21,

    "pc": 4,
    "windows": 4,

    "linux": 6,

    "playstation": 187,
    "ps": 187,

    "xbox": 1,

    "switch": 7,
    "nintendo switch": 7,
}


PLATFORM_LABELS = {
    21: "móvil",
    4: "PC",
    6: "Linux",
    187: "PlayStation",
    1: "Xbox",
    7: "Nintendo Switch",
}


# =========================================================
# ETIQUETAS LEGIBLES PARA LAS EXPLICACIONES
# =========================================================

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
    "indie": "indie",
    "casual": "casual",
    "fighting": "lucha",
    "arcade": "arcade",
    "platformer": "plataformas",
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
    "shared-split-screen": "permite compartir pantalla",

    "singleplayer": "se puede disfrutar en solitario",
    "horror": "encaja con una experiencia de terror",
    "difficult": "ofrece un reto elevado",
    "open-world": "permite explorar un mundo abierto",
    "souls-like": "tiene características souls-like",
    "fast-paced": "propone partidas de ritmo rápido",
    "turn-based": "utiliza mecánicas por turnos",
    "sandbox": "ofrece libertad de exploración y creación",
    "survival": "incluye mecánicas de supervivencia",
}


# =========================================================
# RESTRICCIONES OBLIGATORIAS
# =========================================================
#
# Si el usuario pide explícitamente uno de estos tags,
# el juego debe contenerlo para superar la poda inicial.
#
# co-op se trata por separado en recommendation_engine.py
# para diferenciar cooperativo de multijugador genérico.
# =========================================================

STRICT_TAGS = {
    "story-rich",
    "horror",
    "relaxing",
    "competitive",
    "difficult",
    "open-world",
    "singleplayer",
}


# =========================================================
# SEÑALES ADICIONALES DE COOPERATIVO
# =========================================================
#
# Un juego con "co-op" obtiene nivel 1.
# Si además tiene alguna de estas señales, obtiene nivel 2.
# Esto ayuda a priorizar experiencias cooperativas claras.
# =========================================================

COOP_SUPPORT_TAGS = {
    "online-co-op",
    "local-co-op",
    "couch-co-op",
    "split-screen",
    "shared-split-screen",
    "shared-split-screen-co-op",
    "local-multiplayer",
}


# =========================================================
# PRÓXIMOS LANZAMIENTOS
# =========================================================
#
# ONLY_UNRELEASED_MARKERS:
#   El usuario quiere exclusivamente títulos futuros.
#
# ALLOW_UNRELEASED_MARKERS:
#   El usuario acepta mezclar títulos publicados y futuros.
#
# Importante:
# recommendation_engine.py debe comprobar primero los marcadores
# inclusivos para que "incluyendo próximos" no active por error
# el modo exclusivo.
# =========================================================

ONLY_UNRELEASED_MARKERS = {
    "proximo",
    "proximos",
    "proximamente",
    "futuro",
    "futuros",
    "por salir",
    "upcoming",

    # Catalán
    "proper",
    "propers",
    "proxim",
    "proxims",
    "futur",
    "futurs",
    "per sortir",
}


ALLOW_UNRELEASED_MARKERS = {
    "incluyendo proximos",
    "incluye proximos",
    "tambien proximos",
    "tambien futuros",
    "incluyendo futuros",

    # Catalán
    "incloent proxims",
    "inclou proxims",
    "tambe proxims",
    "tambe futurs",
}