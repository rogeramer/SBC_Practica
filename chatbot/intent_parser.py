INTENT_KEYWORDS = {
    "greeting": ["hola", "buenas", "hey", "hello", "hi"],
    "farewell": ["adios", "adeu", "hasta luego", "bye", "salir", "sortir"],
    "details": ["detalle", "detalles", "info", "informacion", "información", "ficha", "mas info", "más info"],
    "genres": ["generos", "géneros", "tipos", "categorias", "categorías"],
    "platforms": ["plataformas", "consolas", "sistemas"],
    "reset": ["reset", "reiniciar", "empezar de nuevo", "comencem de nou"],
    "help": ["ayuda", "help", "que puedes hacer", "qué puedes hacer", "comandos"],
}


def detect_intent(text: str) -> str:
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return intent
    return "search"