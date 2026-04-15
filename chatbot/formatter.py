import re

def _clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def format_welcome_message():
    return (
        "¡Hola! Soy tu chatbot de videojuegos con RAWG.\n\n"
        "Puedo buscar juegos reales por género, tags, plataformas, rating o nombre.\n\n"
        "Ejemplos:\n"
        "• juegos de accion para pc\n"
        "• rpg con historia\n"
        "• indies relajantes para switch\n"
        "• detalles del 1\n"
        "• generos\n"
        "• plataformas"
    )


def format_help_message():
    return (
        "Puedes pedirme cosas como:\n\n"
        "• juegos de accion para pc\n"
        "• survival horror\n"
        "• rpg para ps5\n"
        "• juegos recientes de 2024\n"
        "• detalles del 2\n"
        "• generos\n"
        "• plataformas\n"
        "• reset"
    )


def format_goodbye_message():
    return "¡Hasta luego! Cuando quieras vuelvo a buscarte juegos."


def format_reset_message():
    return "Contexto reiniciado. Dime qué tipo de juego quieres buscar."


def format_no_results_message():
    return (
        "No he encontrado juegos con esos criterios.\n\n"
        "Prueba con algo como:\n"
        "• juegos de accion para pc\n"
        "• rpg con historia\n"
        "• indies relajantes\n"
        "• top survival horror"
    )


def format_error_message(error):
    return f"Ha ocurrido un error al consultar RAWG: {error}"


def format_genres_list(genres):
    genres = sorted(genres, key=lambda x: x["name"].lower())
    return "Géneros disponibles:\n\n" + "\n".join(
        f"• {g['name']} ({g['slug']})" for g in genres
    )


def format_platforms_list(platforms):
    platforms = sorted(platforms, key=lambda x: x["name"].lower())
    return "Plataformas disponibles:\n\n" + "\n".join(
        f"• {p['name']} (id {p['id']})" for p in platforms
    )


def format_game_card(game, index=None):
    number = f"{index}. " if index is not None else ""
    name = game.get("name", "Sin nombre")
    released = game.get("released") or "Desconocido"
    rating = game.get("rating", "N/A")
    metacritic = game.get("metacritic", "N/A")
    genres = ", ".join(g["name"] for g in game.get("genres", [])[:3]) or "Sin género"
    platforms = ", ".join(
        p["platform"]["name"] for p in game.get("parent_platforms", [])[:3]
    ) or "Sin plataforma"

    return (
        f"{number}🎮 {name}\n"
        f"   • Lanzamiento: {released}\n"
        f"   • Rating RAWG: {rating}\n"
        f"   • Metacritic: {metacritic}\n"
        f"   • Géneros: {genres}\n"
        f"   • Plataformas: {platforms}"
    )


def format_game_list(games, context):
    detected_genres = ", ".join(context["genres"]) if context["genres"] else "sin filtro"
    detected_tags = ", ".join(context["tags"]) if context["tags"] else "sin tags"
    detected_platforms = ", ".join(str(p) for p in context["platforms"]) if context["platforms"] else "sin plataforma"

    intro = (
        f"He encontrado estos juegos.\n"
        f"Filtros actuales: géneros={detected_genres}, tags={detected_tags}, plataformas={detected_platforms}, orden={context['ordering']}.\n\n"
    )

    cards = "\n\n".join(format_game_card(game, i + 1) for i, game in enumerate(games))

    outro = (
        "\n\nPuedes decirme:\n"
        "• detalles del 1\n"
        "• detalles del 2\n"
        "• juegos de estrategia para pc\n"
        "• top rpg"
    )

    return intro + cards + outro


def format_game_details(details):
    genres = ", ".join(g["name"] for g in details.get("genres", [])) or "Sin datos"
    tags = ", ".join(t["name"] for t in details.get("tags", [])[:8]) or "Sin datos"
    developers = ", ".join(d["name"] for d in details.get("developers", [])) or "Sin datos"
    publishers = ", ".join(p["name"] for p in details.get("publishers", [])) or "Sin datos"
    stores = ", ".join(s["store"]["name"] for s in details.get("stores", [])[:6]) or "Sin datos"

    description = _clean_html(details.get("description_raw") or details.get("description") or "")
    if len(description) > 900:
        description = description[:900] + "..."

    return (
        f"📘 {details.get('name', 'Juego')}\n\n"
        f"• Lanzamiento: {details.get('released', 'Desconocido')}\n"
        f"• Rating RAWG: {details.get('rating', 'N/A')}\n"
        f"• Metacritic: {details.get('metacritic', 'N/A')}\n"
        f"• Géneros: {genres}\n"
        f"• Tags: {tags}\n"
        f"• Desarrolladores: {developers}\n"
        f"• Publishers: {publishers}\n"
        f"• Tiendas: {stores}\n"
        f"• Web oficial: {details.get('website') or 'No disponible'}\n\n"
        f"{description or 'Sin descripción disponible.'}"
    )