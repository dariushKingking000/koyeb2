from flask import Flask, request
import requests

BOT_TOKEN = "8407462469:AAG-PgqjnqnvLJyBUa_HwKZwRinPSjWJhpM"

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Mythic AI Store is running 🚀"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text == "/start":
        reply = "👋 خوش اومدی به Mythic AI Store\nربات فعاله 😎"
    else:
        reply = "ربات زنده‌ست ✅"

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": reply
        },
        timeout=10
    )

    return "ok"