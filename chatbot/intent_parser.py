import re
INTENT_KEYWORDS = {
    "greeting": ["hola", "buenas", "hey", "hello"],
    "farewell": ["adios", "adeu", "hasta luego", "bye", "salir", "sortir"],
    "guide": ["como empezar", "ayudame con", "consejos", "como juego", "como jugar", "explica", "guia", "enseña", "consells", "enseñame","guía","dona'm una guia","dame una guia","enseña", "tutorial","tips"],

    "details": ["detalle", "detalles", "info", "informacion", "información",
        "ficha", "mas info", "más info",
        "explica", "explicame", "como jugar", "como juego",
        "guia", "consejos", "como empezar"
    ],

    "genres": ["generos", "géneros", "tipos", "categorias", "categorías"],
    "platforms": ["plataformas", "consolas", "sistemas"],
    "reset": ["reset", "reiniciar", "empezar de nuevo", "comencem de nou"],
    "help": ["ayuda", "help", "que puedes hacer", "qué puedes hacer", "comandos"],
    "most_played": [
        "juego mas jugado",
        "juego más jugado",
        "juegos mas jugados",
        "juegos más jugados",
        "mas jugado",
        "más jugado",
        "mas jugados",
        "más jugados",
        "he jugado mas",
        "he jugado más",
        "mi juego favorito",
        "most played",
        "mes jugats",
        "jocs mes jugats",
        "jocs més jugats"
    ],

    "top_games": [
        # Español
        "mas vendidos",
        "más vendidos",
        "mas populares",
        "más populares",
        "top juegos",
        "juegos populares",
        "juegos movil",
        "juegos móvil",

        # Català
        "mes venuts",
        "més venuts",
        "mes populars",
        "més populars",
        "top jocs",
        "jocs populars",
        "jocs mobil",
        "jocs mòbil",

        # English
        "best selling",
        "best sellers",
        "most popular",
        "top games",
        "popular games",
        "mobile games",
        "best mobile games"
    ]
}

def detect_intent(text: str) -> str:
    text = text.lower()

    for intent, keywords in INTENT_KEYWORDS.items():

        if any(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                text
            )
            for keyword in keywords
        ):
            return intent

    return "search"


