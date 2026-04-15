from flask import *
from main import RuleBasedGameChatbot

app = Flask(__name__)
app.secret_key = "sbc_practica_secret_key"

# Guardarem un bot per sessió de manera simple
bots = {}


def get_bot():
    session_id = session.get("session_id")

    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

    if session_id not in bots:
        bots[session_id] = RuleBasedGameChatbot()

    return bots[session_id]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "Escriu un missatge per començar."})

    bot = get_bot()
    response = bot.respond(message)
    return jsonify({"response": response})


@app.route("/reset", methods=["POST"])
def reset():
    bot = get_bot()
    bot.reset()
    return jsonify({"response": "Conversació reiniciada. Què et ve de gust jugar ara?"})


if __name__ == "__main__":
    app.run(debug=True)