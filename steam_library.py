class SteamLibraryManager:
    def __init__(self, steam_service, rawg_service):
        self.steam = steam_service
        self.rawg = rawg_service

    def load_library(self, steamid: str):
        """
        Carga la biblioteca de Steam y devuelve un resultado normalizado.
        """
        return self.steam.get_owned_games(steamid)

    def build_library_map(self, steam_games):
        """
        Convierte la lista de juegos de Steam en un diccionario por nombre en minúsculas.
        """
        library_map = {}
        for game in steam_games:
            name = (game.get("name") or "").strip().lower()
            if name:
                library_map[name] = game
        return library_map

    def filter_owned_games_from_rawg_results(self, rawg_games, steam_library_map):
        """
        De una lista de resultados de RAWG, devuelve solo los que existen en la biblioteca de Steam.
        El cruce se hace por nombre.
        """
        if not steam_library_map:
            return []

        owned_results = []

        for game in rawg_games:
            rawg_name = (game.get("name") or "").strip().lower()
            if rawg_name in steam_library_map:
                steam_game = steam_library_map[rawg_name]

                merged = dict(game)
                merged["steam_playtime_forever"] = steam_game.get("playtime_forever", 0)
                merged["steam_appid"] = steam_game.get("appid")
                merged["steam_rtime_last_played"] = steam_game.get("rtime_last_played", 0)

                owned_results.append(merged)

        return owned_results

    def recommend_from_library(self, rawg_result, steam_library_map, limit=5, prioritize_less_played=True):
        """
        Cruza resultados RAWG con la biblioteca Steam y devuelve recomendaciones.
        """
        rawg_games = rawg_result.get("results", [])
        owned_games = self.filter_owned_games_from_rawg_results(rawg_games, steam_library_map)

        if prioritize_less_played:
            owned_games.sort(key=lambda g: g.get("steam_playtime_forever", 0))

        return owned_games[:limit]

    def format_library_recommendations(self, games):
        if not games:
            return (
                "No he encontrado coincidencias dentro de tu biblioteca de Steam con esos criterios.\n\n"
                "Prueba con algo como:\n"
                "• un rpg de mi biblioteca\n"
                "• un juego con historia de mi biblioteca\n"
                "• algo de accion de mi biblioteca"
            )

        lines = ["He encontrado estos juegos dentro de tu biblioteca de Steam:\n"]

        for i, game in enumerate(games, start=1):
            playtime = game.get("steam_playtime_forever", 0)
            hours = round(playtime / 60, 1)
            genres = ", ".join(g["name"] for g in game.get("genres", [])[:3]) or "Sin género"

            lines.append(
                f"{i}. 🎮 {game.get('name', 'Sin nombre')}\n"
                f"   • Horas jugadas en Steam: {hours}\n"
                f"   • Rating RAWG: {game.get('rating', 'N/A')}\n"
                f"   • Metacritic: {game.get('metacritic', 'N/A')}\n"
                f"   • Géneros: {genres}\n"
            )

        lines.append(
            "\nPuedes decirme:\n"
            "• detalles del 1\n"
            "• otro juego de mi biblioteca\n"
            "• un juego de accion de mi biblioteca"
        )

        return "\n".join(lines)

    def format_library_loaded_message(self, steamid, game_count):
        return (
            f"Biblioteca de Steam cargada correctamente.\n"
            f"SteamID: {steamid}\n"
            f"Juegos visibles: {game_count}\n\n"
            f"Ahora puedes pedirme cosas como:\n"
            f"• recomiendame algo de mi biblioteca\n"
            f"• un rpg de mi biblioteca\n"
            f"• un juego con historia de mi biblioteca"
        )