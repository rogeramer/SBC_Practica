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
            raise FileNotFoundError("No s'ha trobat el fitxer 'reglas.json'.")

        self.rules = []
        for rule in rules["rules"]:
            self.rules.append({
                "conditions": set(rule["conditions"]),
                "conclusions": set(rule["conclusions"])
            })

        self.guides = rules["guides"]
        self.keyword_map = rules["keyword_map"]
        self.game_names = rules["game_names"]
        self.intents = rules["intents"]

    def reset(self):
        self.facts.clear()

    def preprocess_text(self, text):
        text = text.lower()
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
            "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
            "ü": "u", "ï": "i", "ç": "c"
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"[^\w\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def detect_intent(self, text):
        if any(x in text for x in self.intents["farewell"]):
            return "farewell"
        if any(x in text for x in self.intents["greeting"]):
            return "greeting"
        if any(x in text for x in self.intents["thanks"]):
            return "thanks"
        if any(x in text for x in self.intents["guide"]):
            return "guide"
        if any(x in text for x in self.intents["recommend"]):
            return "recommend"
        if any(x in text for x in self.intents.get("reset", [])):
            return "reset"

        return "unknown"

    def extract_facts(self, text):
        detected = set()

        for phrase, fact in self.keyword_map.items():
            pattern = r'(?:\bno\s+)?\b' + re.escape(phrase) + r'\b'
            matches = re.finditer(pattern, text)

            for match in matches:
                if not match.group().startswith("no "):
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
            if game in text:
                return game
        return None

    def get_recommendations(self):
        all_recommendations = []

        mapping = {
            "recomendar_stardew_valley": "Stardew Valley",
            "recomendar_journey": "Journey",
            "recomendar_life_is_strange": "Life is Strange",
            "recomendar_the_witcher_3": "The Witcher 3",
            "recomendar_valorant": "Valorant",
            "recomendar_rocket_league": "Rocket League",
            "recomendar_minecraft": "Minecraft",
            "recomendar_overcooked_2": "Overcooked 2",
            "recomendar_into_the_breach": "Into the Breach",
            "recomendar_slay_the_spire": "Slay the Spire",
            "recomendar_hades": "Hades",
            "recomendar_dark_souls": "Dark Souls",
            "recomendar_phasmophobia": "Phasmophobia",
            "recomendar_resident_evil_2": "Resident Evil 2",
            "recomendar_dead_cells": "Dead Cells",
            "recomendar_apex_legends": "Apex Legends",
            "recomendar_left_4_dead_2": "Left 4 Dead 2",
            "recomendar_it_takes_two": "It Takes Two",
            "recomendar_valheim": "Valheim",
            "recomendar_civilization_vi": "Civilization VI",
            "recomendar_five_nights_at_freddys": "Five Nights at Freddy's",
            "recomendar_brawl_stars": "Brawl Stars",
            "recomendar_call_of_duty": "Call of Duty",
            "recomendar_solitario": "Solitario",
            "recomendar_clash_royale": "Clash Royale",
            "recomendar_ajedrez": "Ajedrez",
            "recomendar_clash_of_clans": "Clash of Clans",
            "recomendar_fall_guys": "Fall Guys",
            "recomendar_mario_kart": "Mario Kart"
        }

        for rule in self.rules:
            if rule["conditions"].issubset(self.facts):
                for conclusion in rule["conclusions"]:
                    if conclusion in mapping:
                        all_recommendations.append(mapping[conclusion])

        if not all_recommendations:
            return []

        conteo = Counter(all_recommendations)
        juegos_ordenados = [juego for juego, _ in conteo.most_common()]
        return juegos_ordenados

    def ask_for_missing_info(self):
        if not self.facts:
            return (
                "Quin tipus de videojoc busques? Explica'm si vols jugar sol o amb amics, "
                "si prefereixes acció, història, estratègia, por, explorar, partides ràpides o una aventura llarga."
            )

        has_player_count = any(x in self.facts for x in ["solo", "multi"])
        has_vibe = any(x in self.facts for x in ["relajado", "competitivo", "dificil", "poco_tiempo", "mucho_tiempo"])
        has_genre = any(x in self.facts for x in ["historia", "accion", "estrategia", "explorar", "miedo"])

        if not has_player_count:
            return "Entesos. Prefereixes jugar en solitari o en multijugador?"
        if not has_vibe:
            return "Perfecte. Busques una experiència relaxada, competitiva, difícil, ràpida o de moltes hores?"
        if not has_genre:
            return "Ja quasi ho tinc. T'agrada més la història, l'acció, l'estratègia, explorar o els jocs de por?"

        understood = ", ".join(
            [f for f in self.facts if not f.startswith("perfil") and not f.startswith("recomendar")]
        )
        self.facts.clear()
        return (
            f"No he trobat una recomanació prou clara amb aquestes preferències ({understood}). "
            f"Pots provar de reformular-ho o simplificar una mica el que busques."
        )

    def guide_response(self, game):
        if game not in self.guides:
            return "Encara no tinc una guia inicial per aquest joc. Prova amb un altre dels que t'he recomanat."

        tips = self.guides[game]
        res = f"🎮 Consells inicials per a {game.title()}:\n\n"
        for i, tip in enumerate(tips, start=1):
            res += f"{i}. {tip}\n"

        res += "\nQuan vulguis, també et puc recomanar un altre joc."
        return res

    def respond(self, user_input):
        text = self.preprocess_text(user_input)
        intent = self.detect_intent(text)

        if intent == "greeting":
            return (
                "Hola! Sóc el teu chatbot de videojocs. "
                "Et puc recomanar jocs segons els teus gustos o donar-te una guia inicial d'algun joc concret."
            )

        if intent == "farewell":
            return "Fins aviat! Quan vulguis tornar a buscar un joc, aquí estaré."

        if intent == "thanks":
            self.facts.clear()
            return "De res! Encantat d'ajudar-te 🎮"

        if intent == "reset":
            self.facts.clear()
            return "Perfecte, comencem de nou. Què et ve de gust jugar ara?"

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
                return "Clar. De quin dels jocs que t'he dit vols una guia inicial?"
            else:
                return "Digues-me primer quin joc vols o deixa'm recomanar-te'n un."

        if any(f.startswith("recomendar_") for f in self.facts):
            self.facts.clear()

        new_facts = self.extract_facts(text)
        self.facts.update(new_facts)

        prefix = ""
        if intent == "recommend" and self.facts:
            prefix = "Perfecte, ho miro. "

        self.forward_chaining()
        recommendations = self.get_recommendations()

        if recommendations:
            top_3 = recommendations[:3]
            resto = recommendations[3:]

            ans = prefix + "Et recomano: " + ", ".join(top_3) + "."
            if resto:
                ans += "\n\nTambé et podrien agradar: " + ", ".join(resto) + "."

            if len(recommendations) == 1:
                ans += "\n\nSi vols, et puc explicar com començar a jugar-hi."
            else:
                ans += "\n\nSi vols, et puc donar una guia inicial d'algun d'aquests jocs."

            return ans

        return prefix + self.ask_for_missing_info()


def main():
    bot = RuleBasedGameChatbot()

    print("--- Chatbot de Videojocs Iniciat ---")
    print("Escriu 'sortir' per acabar.\n")

    while True:
        user_input = input("Tu: ")
        clean = bot.preprocess_text(user_input)

        if clean in ["sortir", "salir", "adios", "adeu", "hasta luego", "bye"]:
            print("Bot: Fins aviat! Per qualsevol altra consulta, aquí estaré.")
            break

        print("Bot:", bot.respond(user_input))


if __name__ == "__main__":
    main()