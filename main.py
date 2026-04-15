import re
import json
from collections import Counter

class RuleBasedGameChatbot:
    def __init__(self):
        self.facts = set()
        try:
            with open("reglas.json", "r", encoding="utf-8") as file:
                rules = json.load(file)
        except FileNotFoundError:
            print("Error: No se ha encontrado el archivo 'reglas.json'.")
            exit()
        self.rules = []
        for rule in rules["rules"]:
            self.rules.append({
                "conditions": set(rule["conditions"]),
                "conclusions": set(rule["conclusions"])
                # Eliminada la clave "priority"
            })

        self.guides = rules["guides"]
        self.keyword_map = rules["keyword_map"]
        self.game_names = rules["game_names"]
        self.intents = rules["intents"]

    def preprocess_text(self, text):
        text = text.lower()
        replacements = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "à": "a", "è": "e", "ì": "i", "ò": "o",
                        "ù": "u", "ü": "u"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"[^\w\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def detect_intent(self, text):
        if any(x in text for x in self.intents["farewell"]): return "farewell"
        if any(x in text for x in self.intents["greeting"]): return "greeting"
        if any(x in text for x in self.intents["thanks"]): return "thanks"
        if any(x in text for x in self.intents["guide"]): return "guide"
        if any(x in text for x in self.intents["recommend"]): return "recommend"
        if any(x in text for x in self.intents.get("reset", [])): return "reset"

        return "unknown"

    def extract_facts(self, text):
        detected = set()
        for phrase, fact in self.keyword_map.items():
            pattern = r'(?:\bno\s+)?\b' + re.escape(phrase) + r'\b'
            matches = re.finditer(pattern, text)
            for match in matches:
                if not match.group().startswith('no '):
                    detected.add(fact)
        return detected

    def forward_chaining(self):
        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                if rule["conditions"].issubset(self.facts):
                    for conclusion in rule["conclusions"]:
                        if conclusion not in self.facts:
                            self.facts.add(conclusion)
                            changed = True

    def detect_game_in_text(self, text):
        for game in self.game_names:
            if game in text: return game
        return None

    def get_recommendations(self):
        all_recommendations = []
        mapping = {
            "recomendar_stardew_valley": "Stardew Valley", "recomendar_journey": "Journey",
            "recomendar_life_is_strange": "Life is Strange", "recomendar_the_witcher_3": "The Witcher 3",
            "recomendar_valorant": "Valorant", "recomendar_rocket_league": "Rocket League",
            "recomendar_minecraft": "Minecraft", "recomendar_overcooked_2": "Overcooked 2",
            "recomendar_into_the_breach": "Into the Breach", "recomendar_slay_the_spire": "Slay the Spire",
            "recomendar_hades": "Hades", "recomendar_dark_souls": "Dark Souls",
            "recomendar_phasmophobia": "Phasmophobia", "recomendar_resident_evil_2": "Resident Evil 2",
            "recomendar_dead_cells": "Dead Cells", "recomendar_apex_legends": "Apex Legends",
            "recomendar_left_4_dead_2": "Left 4 Dead 2", "recomendar_it_takes_two": "It Takes Two",
            "recomendar_valheim": "Valheim", "recomendar_civilization_vi": "Civilization VI",
            "recomendar_five_nights_at_freddys": "Five Nights at Freddy's",
            "recomendar_brawl_stars": "Brawl Stars", "recomendar_call_of_duty": "Call of Duty",
            "recomendar_solitario": "Solitario", "recomendar_clash_royale": "Clash Royale",
            "recomendar_ajedrez": "Ajedrez", "recomendar_clash_of_clans": "Clash of Clans",
            "recomendar_fall_guys": "Fall Guys", "recomendar_mario_kart": "Mario Kart"
        }

        for rule in self.rules:
            if rule["conditions"].issubset(self.facts):
                for conclusion in rule["conclusions"]:
                    if conclusion in mapping:
                        all_recommendations.append(mapping[conclusion])

        if not all_recommendations:
            return []

        conteo = Counter(all_recommendations)
        juegos_ordenados = [juego for juego, puntuacion in conteo.most_common()]

        return juegos_ordenados

    def ask_for_missing_info(self):
        if not self.facts:
            return "¿Qué tipo de videojuego buscas? Dime tus preferencias para encontrarte el mejor juego ahora mismo."

        has_player_count = any(x in self.facts for x in ["solo", "multi"])
        has_vibe = any(x in self.facts for x in ["relajado", "competitivo", "dificil", "poco_tiempo", "mucho_tiempo"])
        has_genre = any(x in self.facts for x in ["historia", "accion", "estrategia", "explorar", "miedo"])

        if not has_player_count: return "Vale, veo por dónde vas. Pero, ¿prefieres jugar en solitario o en multijugador?"
        if not has_vibe: return "Entendido. ¿Buscas algo relajado, un buen reto, partidas cortas o prefieres un juego largo para echarle horas?"
        if not has_genre: return "Casi lo tengo. ¿Qué temática te apetece más: historia, acción, estrategia, explorar o pasar miedo?"

        understood = ", ".join([f for f in self.facts if not f.startswith("perfil") and not f.startswith("recomendar")])
        self.facts.clear()
        return f"Lo siento, me has pedido algo muy concreto ({understood}) y mi base de datos no tiene nada que cuadre 100% con tus requisitos."

    def guide_response(self, game):
        if game not in self.guides:
            return "Todavía no tengo una guía para ese juego. Puedo ayudarte con otros."
        tips = self.guides[game]
        res = f"Consejos iniciales para {game.title()}:\n"
        for i, tip in enumerate(tips, start=1): res += f"{i}. {tip}\n"

        res += "\n¡Espero que estos consejos te sirvan!"
        return res

    def respond(self, user_input):
        text = self.preprocess_text(user_input)
        intent = self.detect_intent(text)
        if intent == "greeting": return (
            "¡Hola! Soy un chatbot experto en videojuegos. Te puedo sugerir videojuegos según "
            "tus necesidades o darte algunos consejos iniciales.")
        if intent == "farewell":
            return "¡Hasta luego! Aquí estaré."
        if intent == "thanks":
            self.facts.clear()
            return "¡De nada! Me alegra poder haberte ayudado."
        if intent == "reset":
            self.facts.clear()
            return "¡Empecemos de nuevo! ¿Qué te apetece jugar ahora?"

        game = self.detect_game_in_text(text)
        if intent == "guide" and game:
            respuesta = self.guide_response(game)
            self.facts.clear()
            return respuesta

        if game and not any(x in text for x in self.keyword_map.keys()):
            respuesta = self.guide_response(game)
            self.facts.clear()
            return respuesta

        if intent == "guide" and not game:
            juegos_actuales = self.get_recommendations()

            if len(juegos_actuales) == 1:
                juego_unico = juegos_actuales[0].lower()
                respuesta = self.guide_response(juego_unico)
                self.facts.clear()
                return respuesta
            elif len(juegos_actuales) > 1:
                return "Claro. ¿De cuál de los juegos que te he mencionado quieres consejos?"
            else:
                return "Claro. ¿De qué juego quieres unos consejos?"

        if any(f.startswith("recomendar_") for f in self.facts):
            self.facts.clear()

        new_facts = self.extract_facts(text)
        self.facts.update(new_facts)
        prefix = "¡Perfecto! Vamos a buscarte algo. " if intent == "recommend" and not self.facts else ""
        self.forward_chaining()
        recommendations = self.get_recommendations()

        if recommendations:
            top_3 = recommendations[:3]
            resto = recommendations[3:]
            ans = "¡Lo tengo! Te recomiendo: " + ", ".join(top_3) + "."
            if len(recommendations) > 3:
                ans += "\nPero también te puede interesar: " + ", ".join(resto) + "."
            if len(recommendations) == 1:
                ans += "\nPuedes pedirme que te explique cómo empezar a jugarlo."
            else:
                ans += "\nPuedes pedirme que te explique cómo empezar a jugar a alguno de ellos."
            return ans
        return prefix + self.ask_for_missing_info()

def main():
    bot = RuleBasedGameChatbot()
    print("--- Chatbot de Videojuegos Iniciado ---")
    print("Escribe 'salir' para terminar.\n")
    while True:
        user_input = input("Tú: ")
        clean = bot.preprocess_text(user_input)
        if clean in ["salir", "adios", "hasta luego", "bye"]:
            print("Bot: ¡Hasta luego! Para cualquier otra consulta aquí estaré.")
            break
        print("Bot:", bot.respond(user_input))

if __name__ == "__main__":
    main()