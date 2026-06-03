import html
import random
import re

from chatbot.recommendation_config import (
    PLATFORM_LABELS,
)

INTRO_MESSAGES = [
    "Perfecto, creo que estos juegos te pueden gustar:",
    "Basado en lo que buscas, te recomiendo:",
    "He encontrado algunos juegos interesantes para ti:",
]

def _clean_html(text):
    if not text:
        return ""

    text = html.unescape(
        str(text)
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    return text.strip()


def _display_value(value, fallback="No disponible"):
    if value is None or value == "":
        return fallback

    return value

def _join_names(items, limit=None):
    if limit is not None:
        items = items[:limit]

    names = [
        item.get("name")
        for item in items
        if item.get("name")
    ]

    return ", ".join(
        names
    )

def _join_store_names(stores, limit=None):
    if limit is not None:
        stores = stores[:limit]

    names = []

    for item in stores:
        store = item.get(
            "store",
            {},
        )

        name = store.get("name")

        if name:
            names.append(name)

    return ", ".join(
        names
    )

def _join_game_platform_names(game, limit=5):
    names = []

    for item in game.get(
        "platforms",
        [],
    )[:limit]:
        platform = item.get(
            "platform",
            {},
        )

        name = platform.get("name")

        if name:
            names.append(name)

    return ", ".join(
        names
    )

def _format_selected_platforms(context):
    if not context:
        return ""

    selected_platforms = set(
        context.get("explicit_platforms")
        or context.get("platforms")
        or []
    )

    if not selected_platforms:
        return ""

    labels = [
        PLATFORM_LABELS.get(platform_id)
        for platform_id in selected_platforms
        if PLATFORM_LABELS.get(platform_id)
    ]

    return ", ".join(
        sorted(labels)
    )

def format_reasons_text(reasons):
    cleaned_reasons = []

    for reason in reasons:
        reason = str(
            reason
        ).strip()

        if not reason:
            continue

        reason = (
            reason[0].upper()
            + reason[1:]
        )

        cleaned_reasons.append(
            reason.rstrip(".")
        )

    if not cleaned_reasons:
        return ""

    return ". ".join(
        cleaned_reasons
    ) + "."

def format_welcome_message():
    return (
        "¡Hola! Soy tu chatbot de videojuegos con RAWG.\n\n"
        "Puedo buscar juegos reales por género, etiquetas, "
        "plataformas, valoración o nombre.\n\n"
        "También puedo recomendar juegos de tu biblioteca de Steam "
        "si cargas un SteamID64 público.\n\n"
        "Ejemplos:\n"
        "• juegos de acción para PC\n"
        "• RPG con historia\n"
        "• indies relajantes para Switch\n"
        "• recomiéndame un cooperativo local\n"
        "• detalles del 1\n"
        "• géneros\n"
        "• plataformas"
    )

def format_help_message():
    return (
        "Puedes pedirme cosas como:\n\n"
        "• juegos de acción para PC\n"
        "• survival horror\n"
        "• RPG para PS5\n"
        "• juegos recientes de 2024\n"
        "• próximos RPG para PC\n"
        "• un cooperativo online\n"
        "• detalles del 2\n"
        "• géneros\n"
        "• plataformas\n"
        "• reset\n\n"
        "Steam:\n"
        "• cargar steam 7656119XXXXXXXXXX\n"
        "• recomiéndame algo de mi biblioteca\n"
        "• dime mis juegos más jugados"
    )

def format_goodbye_message():
    return (
        "¡Hasta luego! "
        "Cuando quieras vuelvo a buscarte juegos."
    )

def format_reset_message():
    return (
        "Contexto reiniciado. "
        "Dime qué tipo de juego quieres buscar."
    )

def format_no_results_message():
    return (
        "No he encontrado juegos que encajen con esos criterios.\n\n"
        "Prueba a simplificar la búsqueda. Por ejemplo:\n"
        "• juegos de acción para PC\n"
        "• RPG con historia\n"
        "• indies relajantes\n"
        "• cooperativos para jugar con amigos"
    )

def format_error_message(error):
    return (
        "Ha ocurrido un error al procesar la consulta: "
        f"{error}"
    )

def format_genres_list(genres):
    genres = sorted(
        genres,
        key=lambda item: item.get(
            "name",
            "",
        ).lower(),
    )

    lines = [
        f"• {genre.get('name', 'Sin nombre')} "
        f"({genre.get('slug', 'sin-slug')})"
        for genre in genres
    ]

    return (
        "Géneros disponibles:\n\n"
        + "\n".join(lines)
    )

def format_platforms_list(platforms):
    platforms = sorted(
        platforms,
        key=lambda item: item.get(
            "name",
            "",
        ).lower(),
    )
    lines = [
        f"• {platform.get('name', 'Sin nombre')} "
        f"(id {platform.get('id', 'N/A')})"
        for platform in platforms
    ]

    return (
        "Plataformas disponibles:\n\n"
        + "\n".join(lines)
    )

def format_game_card(
    game,
    context=None,
    index=None,
):
    number = (
        f"{index}. "
        if index is not None
        else ""
    )
    name = _display_value(
        game.get("name"),
        "Sin nombre",
    )
    released = _display_value(
        game.get("released"),
        "Sin fecha confirmada",
    )
    rating = _display_value(
        game.get("rating"),
        "No disponible",
    )
    metacritic = _display_value(
        game.get("metacritic"),
        "No disponible",
    )
    genres = (
        _join_names(
            game.get(
                "genres",
                [],
            ),
            limit=3,
        )
        or "Sin género"
    )
    selected_platforms = (
        _format_selected_platforms(
            context
        )
    )
    if selected_platforms:
        platforms = selected_platforms

    else:
        platforms = (
            _join_game_platform_names(
                game,
                limit=5,
            )
            or "Sin plataforma"
        )
    reasons = game.get(
        "_recommendation_reasons",
        [],
    )
    reasons_text = ""
    if reasons:
        reasons_text = (
            "\n"
            "   • Por qué encaja: "
            f"{format_reasons_text(reasons)}"
        )
    return (
        f"{number}🎮 {name}\n"
        f"   • Lanzamiento: {released}\n"
        f"   • Rating RAWG: {rating}\n"
        f"   • Metacritic: {metacritic}\n"
        f"   • Géneros: {genres}\n"
        f"   • Plataformas: {platforms}"
        f"{reasons_text}"
    )

def format_game_list(
    games,
    context,
):
    if not games:
        return format_no_results_message()
    intro = random.choice(
        INTRO_MESSAGES
    )
    cards = "\n\n".join(
        format_game_card(
            game,
            context,
            index + 1,
        )
        for index, game in enumerate(
            games
        )
    )
    outro = (
        "\n\n¿Quieres que te explique "
        "de qué trata alguno?"
    )
    return (
        intro
        + "\n\n"
        + cards
        + outro
    )

def format_game_details(details):
    genres = (
        _join_names(
            details.get(
                "genres",
                [],
            )
        )
        or "Sin datos"
    )
    tags = (
        _join_names(
            details.get(
                "tags",
                [],
            ),
            limit=8,
        )
        or "Sin datos"
    )
    developers = (
        _join_names(
            details.get(
                "developers",
                [],
            )
        )
        or "Sin datos"
    )
    publishers = (
        _join_names(
            details.get(
                "publishers",
                [],
            )
        )
        or "Sin datos"
    )
    stores = (
        _join_store_names(
            details.get(
                "stores",
                [],
            ),
            limit=6,
        )
        or "Sin datos"
    )
    description = _clean_html(
        details.get("description_raw")
        or details.get("description")
        or ""
    )
    if len(description) > 900:
        description = (
            description[:900]
            + "..."
        )

    return (
        f"{_display_value(details.get('name'), 'Juego')}\n\n"
        f"• Lanzamiento: "
        f"{_display_value(details.get('released'), 'Sin fecha confirmada')}\n"
        f"• Rating RAWG: "
        f"{_display_value(details.get('rating'))}\n"
        f"• Metacritic: "
        f"{_display_value(details.get('metacritic'))}\n"
        f"• Géneros: {genres}\n"
        f"• Tags: {tags}\n"
        f"• Desarrolladores: {developers}\n"
        f"• Publishers: {publishers}\n"
        f"• Tiendas: {stores}\n"
        f"• Web oficial: "
        f"{_display_value(details.get('website'))}\n\n"
        f"{description or 'Sin descripción disponible.'}"
    )