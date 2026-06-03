import re
import unicodedata

INTENT_KEYWORDS = [
    (
        "reset",
        [
            "reset",
            "reiniciar",
            "reinicia",
            "empezar de nuevo",
            "comenzar de nuevo",
            "reinicia la conversacion",
        ],
    ),

    (
        "more_results",
        [
            "otros cinco",
            "otros 5",
            "dame otros cinco",
            "dame otros 5",
            "mas juegos",
            "mas recomendaciones",
            "quiero mas",
            "otro juego",
            "otros juegos",
            "siguiente",
            "siguientes",
        ],
    ),

    (
        "most_played",
        [
            "juego que mas he jugado",
            "juegos que mas he jugado",
            "cual es el juego que mas he jugado",
            "dime el juego que mas he jugado",
            "dime los juegos que mas he jugado",
            "juego mas jugado",
            "juegos mas jugados",
            "mi juego favorito",
            "most played",
        ],
    ),

    (
        "top_games",
        [
            "top juegos para movil",
            "top juegos movil",
            "mejores juegos para movil",
            "juegos populares movil",
            "mobile games",
            "best mobile games",
        ],
    ),

    (
        "tips",
        [
            "dame consejos",
            "quiero consejos",
            "consejos para",
            "tips para",
            "tips de",
            "como empezar",
            "ayudame a empezar",
        ],
    ),

    (
        "guide",
        [
            "dame una guia",
            "quiero una guia",
            "guia de",
            "guia del",
            "explicame de que trata",
            "de que trata",
        ],
    ),

    (
        "details",
        [
            "detalles del",
            "detalles de",
            "detalle del",
            "detalle de",
            "informacion del",
            "informacion de",
            "info del",
            "info de",
            "ficha del",
            "ficha de",
        ],
    ),

    (
        "genres",
        [
            "generos",
            "lista de generos",
            "que generos hay",
            "tipos de juegos",
        ],
    ),

    (
        "platforms",
        [
            "plataformas",
            "lista de plataformas",
            "que plataformas hay",
            "consolas",
            "sistemas",
        ],
    ),

    (
        "help",
        [
            "ayuda",
            "help",
            "que puedes hacer",
            "que sabes hacer",
            "comandos",
        ],
    ),

    (
        "greeting",
        [
            "hola",
            "buenas",
            "buenos dias",
            "buenas tardes",
            "buenas noches",
            "hey",
            "hello",
        ],
    ),

    (
        "farewell",
        [
            "adios",
            "hasta luego",
            "nos vemos",
            "bye",
            "salir",
        ],
    ),
]


def _normalize_text(text):
    text = str(
        text or ""
    ).lower()

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


def _contains_phrase(
    text,
    phrase,
):
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


def detect_intent(text):
    clean_text = _normalize_text(
        text
    )

    for intent, keywords in INTENT_KEYWORDS:
        for keyword in sorted(
            keywords,
            key=len,
            reverse=True,
        ):
            if _contains_phrase(
                clean_text,
                keyword,
            ):
                return intent

    return "search"