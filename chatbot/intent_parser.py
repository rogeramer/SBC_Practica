import re
import unicodedata


# =========================================================
# INTENCIONES
# =========================================================
#
# El orden importa:
# - primero acciones específicas;
# - después comandos generales;
# - al final saludos y despedidas.
#
# Las expresiones se escriben sin acentos porque el texto
# se normaliza antes de buscar coincidencias.
# =========================================================

INTENT_KEYWORDS = [
    (
        "reset",
        [
            "reset",
            "reiniciar",
            "reinicia",
            "empezar de nuevo",
            "comenzar de nuevo",
            "comencem de nou",
            "reinicia la conversacion",
            "reinicia conversa",
        ],
    ),

    (
        "most_played",
        [
            # Español
            "juego que mas he jugado",
            "juegos que mas he jugado",
            "cual es el juego que mas he jugado",
            "cuales son los juegos que mas he jugado",
            "dime el juego que mas he jugado",
            "dime los juegos que mas he jugado",
            "juego mas jugado",
            "juegos mas jugados",
            "he jugado mas",
            "mi juego favorito",

            # Catalán
            "joc que mes he jugat",
            "jocs que mes he jugat",
            "quin joc he jugat mes",
            "quins jocs he jugat mes",
            "joc mes jugat",
            "jocs mes jugats",

            # Inglés
            "most played",
            "my most played game",
            "my most played games",
        ],
    ),

    (
        "top_games",
        [
            # Esta intención se reserva para rankings móviles.
            # Las peticiones genéricas como "juegos populares"
            # pasarán por el buscador normal con ordering=-added.

            # Español
            "top juegos movil",
            "top juegos para movil",
            "mejores juegos movil",
            "mejores juegos para movil",
            "juegos populares movil",
            "juegos para movil",

            # Catalán
            "top jocs mobil",
            "top jocs per mobil",
            "millors jocs mobil",
            "millors jocs per mobil",
            "jocs populars mobil",
            "jocs per mobil",

            # Inglés
            "top mobile games",
            "best mobile games",
            "popular mobile games",
            "mobile games",
        ],
    ),

    (
        "guide",
        [
            # Español
            "dame una guia",
            "quiero una guia",
            "guia de",
            "como empezar",
            "como jugar",
            "tutorial",
            "consejos para",
            "tips para",
            "ayudame con",

            # Catalán
            "dona m una guia",
            "vull una guia",
            "guia de",
            "com comencar",
            "com jugar",
            "consells per",

            # Inglés
            "guide for",
            "guide to",
            "how to start",
            "how to play",
            "tutorial for",
            "tips for",
        ],
    ),

    (
        "details",
        [
            # Español
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
            "de que trata",
            "explicame el juego",
            "explicame de que trata",

            # Catalán
            "detalls del",
            "detalls de",
            "informacio del",
            "informacio de",
            "de que tracta",

            # Inglés
            "details of",
            "information about",
            "tell me about",
        ],
    ),

    (
        "genres",
        [
            "generos",
            "lista de generos",
            "que generos hay",
            "tipos de juegos",
            "categories",
            "categories disponibles",
            "genres",
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
            "plataformes",
            "platforms",
        ],
    ),

    (
        "help",
        [
            "ayuda",
            "help",
            "que puedes hacer",
            "que sabes hacer",
            "como funcionas",
            "comandos",
            "ajuda",
            "que pots fer",
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
            "hi",
            "ei",
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
            "adeu",
            "fins despres",
            "sortir",
        ],
    ),
]


# =========================================================
# NORMALIZACIÓN
# =========================================================

def _normalize_text(text):
    """
    Normaliza el texto antes de detectar intenciones.

    Ejemplos:
    - "Guía de Minecraft" → "guia de minecraft"
    - "¿Qué puedes hacer?" → "que puedes hacer"
    - "dona'm una guia" → "dona m una guia"
    """

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


def _contains_phrase(text, phrase):
    """
    Comprueba que la frase aparezca completa.

    Evita falsos positivos como:
    - "hi" dentro de "historia";
    - "info" dentro de otra palabra.
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
# DETECCIÓN
# =========================================================

def detect_intent(text):
    """
    Detecta la intención principal del mensaje.

    Devuelve:
    - reset
    - most_played
    - top_games
    - guide
    - details
    - genres
    - platforms
    - help
    - greeting
    - farewell
    - search
    """

    clean_text = _normalize_text(
        text
    )

    for intent, keywords in INTENT_KEYWORDS:
        sorted_keywords = sorted(
            keywords,
            key=len,
            reverse=True,
        )

        for keyword in sorted_keywords:
            if _contains_phrase(
                clean_text,
                keyword,
            ):
                return intent

    return "search"
