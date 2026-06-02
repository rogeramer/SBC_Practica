from flask import Flask, render_template, request, jsonify, session
from main import RawgGameChatbot
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

app = Flask(__name__)

# Clave secreta para gestionar la sesión del usuario.
# En el .env deberías tener algo como:
# FLASK_SECRET_KEY=una_clave_larga_y_aleatoria
app.secret_key = os.getenv("FLASK_SECRET_KEY", "sbc_practica_secret")

# Diccionario simple para guardar un chatbot por sesión.
# Para una práctica local está bien.
bots = {}


def get_bot():
    """
    Devuelve el chatbot asociado a la sesión actual.
    Si no existe sesión, crea una nueva.
    """

    session_id = session.get("session_id")

    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

    if session_id not in bots:
        bots[session_id] = RawgGameChatbot()

    return bots[session_id]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Recibe el mensaje del usuario desde el frontend,
    lo pasa al chatbot y devuelve la respuesta en JSON.
    """

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "response": "Escribe un mensaje para empezar."
        })

    bot = get_bot()
    response = bot.respond(message)

    return jsonify({
        "response": response
    })


@app.route("/reset", methods=["POST"])
def reset():
    """
    Reinicia el contexto conversacional del chatbot
    asociado a la sesión actual.
    """

    bot = get_bot()
    bot.reset()

    return jsonify({
        "response": "Conversación reiniciada. ¿Qué juego quieres buscar ahora?"
    })


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug_mode)