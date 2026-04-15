from flask import Flask, render_template, request, jsonify, session
from main import RawgGameChatbot
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "sbc_practica_secret")

bots = {}


def get_bot():
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
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "Escribe un mensaje para empezar."})

    bot = get_bot()
    response = bot.respond(message)
    return jsonify({"response": response})


@app.route("/reset", methods=["POST"])
def reset():
    bot = get_bot()
    bot.reset()
    return jsonify({"response": "Conversación reiniciada. ¿Qué juego quieres buscar ahora?"})


if __name__ == "__main__":
    app.run(debug=True)