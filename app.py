import os
import logging
import threading
import requests
from flask import Flask, request, jsonify

# ---------- Configuration ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None

APP_NAME = "Mythic AI Store"

DEFAULT_DEMO_IMAGE = "https://via.placeholder.com/1024x768.png?text=Demo+Image"
DEFAULT_DEMO_VIDEO = "https://via.placeholder.com/1280x720.png?text=Demo+Video"

PACKS = {
    "img_001": {
        "id": "img_001",
        "title": "Anime Pack (10 images)",
        "description": "High-quality AI-generated anime images.",
        "type": "image",
        "demo_url": DEFAULT_DEMO_IMAGE,
    },
    "img_002": {
        "id": "img_002",
        "title": "Realistic Pack (8 images)",
        "description": "Photorealistic AI images.",
        "type": "image",
        "demo_url": DEFAULT_DEMO_IMAGE,
    },
    "vid_001": {
        "id": "vid_001",
        "title": "Cinematic Video Pack",
        "description": "Short cinematic AI video.",
        "type": "video",
        "demo_url": DEFAULT_DEMO_VIDEO,
    }
}

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mythic-bot")

# ---------- Flask ----------
app = Flask(__name__)

# ---------- Telegram helpers ----------
def telegram_request(method, payload):
    if not API_URL:
        logger.error("BOT_TOKEN is not set")
        return

    url = f"{API_URL}/{method}"
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        logger.exception("Telegram request failed: %s", e)


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    telegram_request("sendMessage", payload)


def send_photo(chat_id, photo, caption=None, reply_markup=None):
    payload = {"chat_id": chat_id, "photo": photo}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    if reply_markup:
        payload["reply_markup"] = reply_markup
    telegram_request("sendPhoto", payload)


def answer_callback(cq_id):
    telegram_request("answerCallbackQuery", {"callback_query_id": cq_id})


# ---------- Keyboards ----------
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🖼 Image Packs", "callback_data": "images"}],
            [{"text": "🎥 Video Packs", "callback_data": "videos"}],
            [{"text": "🎁 Demo", "callback_data": "demo"}],
            [{"text": "ℹ️ About", "callback_data": "about"}],
        ]
    }


def packs_keyboard(p_type):
    kb = []
    for p in PACKS.values():
        if p["type"] == p_type:
            kb.append([{"text": p["title"], "callback_data": f"pack:{p['id']}"}])
    kb.append([{"text": "🔙 Back", "callback_data": "back"}])
    return {"inline_keyboard": kb}


def pack_actions(pack_id):
    return {
        "inline_keyboard": [
            [{"text": "📤 Demo Preview", "callback_data": f"demo_pack:{pack_id}"}],
            [{"text": "🔙 Back", "callback_data": "back"}],
        ]
    }


# ---------- Core Logic ----------
def handle_update(update):
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            send_message(
                chat_id,
                f"👋 <b>Welcome to {APP_NAME}</b>\nChoose:",
                reply_markup=main_menu()
            )

    elif "callback_query" in update:
        q = update["callback_query"]
        data = q["data"]
        chat_id = q["message"]["chat"]["id"]

        answer_callback(q["id"])

        if data == "images":
            send_message(chat_id, "🖼 Image Packs:", packs_keyboard("image"))

        elif data == "videos":
            send_message(chat_id, "🎥 Video Packs:", packs_keyboard("video"))

        elif data == "demo":
            send_photo(chat_id, DEFAULT_DEMO_IMAGE, "🎁 Free demo image")

        elif data == "about":
            send_message(chat_id, "🤖 Mythic AI Store\nAI-generated image & video packs.")

        elif data == "back":
            send_message(chat_id, "Main menu:", main_menu())

        elif data.startswith("pack:"):
            pid = data.split(":")[1]
            p = PACKS.get(pid)
            if p:
                send_photo(
                    chat_id,
                    p["demo_url"],
                    f"<b>{p['title']}</b>\n{p['description']}",
                    pack_actions(pid)
                )

        elif data.startswith("demo_pack:"):
            pid = data.split(":")[1]
            p = PACKS.get(pid)
            if p:
                send_photo(chat_id, p["demo_url"], "📤 Demo preview")


# ---------- Routes ----------
@app.route("/")
def index():
    return f"{APP_NAME} is running 🚀"


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    threading.Thread(target=handle_update, args=(update,)).start()
    return "ok", 200


# ---------- Run ----------
if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is NOT set")
    app.run(host="0.0.0.0", port=8000)