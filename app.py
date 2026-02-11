# app.py
import os
import logging
import requests
from flask import Flask, request, jsonify

# ---------- Configuration ----------
BOT_TOKEN = os.getenv("8407462469:AAG-PgqjnqnvLJyBUa_HwKZwRinPSjWJhpM")  # set this in environment variables on Koyeb
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None
APP_NAME = "Mythic AI Store"
DEFAULT_DEMO_IMAGE = "https://via.placeholder.com/1024x768.png?text=Demo+Image"
DEFAULT_DEMO_VIDEO = "https://via.placeholder.com/1280x720.png?text=Demo+Video+Preview"

# In-memory data (fake/demo). Replace with a DB or real storage later.
PACKS = {
    "img_001": {
        "id": "img_001",
        "title": "Anime Pack (10 images)",
        "description": "High-quality AI-generated anime style images (demo).",
        "price": "5 USDT (demo)",
        "type": "image",
        "demo_url": DEFAULT_DEMO_IMAGE,
    },
    "img_002": {
        "id": "img_002",
        "title": "Realistic Pack (8 images)",
        "description": "Photorealistic AI images (demo).",
        "price": "7 USDT (demo)",
        "type": "image",
        "demo_url": DEFAULT_DEMO_IMAGE,
    },
    "vid_001": {
        "id": "vid_001",
        "title": "Cinematic Video Pack (1 clip)",
        "description": "Short cinematic AI video (demo preview).",
        "price": "10 USDT (demo)",
        "type": "video",
        "demo_url": DEFAULT_DEMO_VIDEO,
    }
}

ORDERS = {}  # simulated orders: order_id -> data

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mythic-bot")

# ---------- Flask app ----------
app = Flask(__name__)


# ---------- HTTP helpers ----------
def telegram_request(method: str, payload: dict):
    """POST JSON to Telegram Bot API and return parsed json or None on error."""
    if not API_URL:
        logger.error("BOT_TOKEN environment variable is not set.")
        return None

    url = f"{API_URL}/{method}"
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        j = resp.json()
        if not j.get("ok"):
            logger.warning("Telegram API returned ok=false: %s", j)
        return j
    except Exception as e:
        logger.exception("Failed Telegram request %s: %s", url, e)
        return None


def send_message(chat_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_request("sendMessage", payload)


def send_photo(chat_id: int, photo_url: str, caption: str = None, reply_markup: dict = None):
    payload = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_request("sendPhoto", payload)


def answer_callback(callback_query_id: str, text: str = None, show_alert: bool = False):
    payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    return telegram_request("answerCallbackQuery", payload)


# ---------- Keyboard builders ----------
def main_menu_keyboard():
    keyboard = {
        "inline_keyboard": [
            [{"text": "🖼 Image Packs", "callback_data": "menu_images"}],
            [{"text": "🎥 Video Packs", "callback_data": "menu_videos"}],
            [{"text": "🎁 Free Demo", "callback_data": "menu_demo"}],
            [{"text": "ℹ️ About", "callback_data": "menu_about"}],
        ]
    }
    return keyboard


def packs_keyboard(pack_type=None):
    buttons = []
    for pack in PACKS.values():
        if pack_type and pack["type"] != pack_type:
            continue
        buttons.append([{"text": pack["title"], "callback_data": f"pack:{pack['id']}"}])
    # Add back button
    buttons.append([{"text": "🔙 Back", "callback_data": "back_main"}])
    return {"inline_keyboard": buttons}


def pack_actions_keyboard(pack_id):
    return {
        "inline_keyboard": [
            [{"text": "📤Free Demo", "callback_data": f"demo:{pack_id}"}],
            [{"text": "💳 Buy (simulate)", "callback_data": f"buy:{pack_id}"}],
            [{"text": "🔙 Back to Packs", "callback_data": "back_packs"}],
        ]
    }


def buy_confirm_keyboard(order_id):
    return {
        "inline_keyboard": [
            [{"text": "✅ Mark Paid (simulate)", "callback_data": f"paid:{order_id}"}],
            [{"text": "❌ Cancel Order", "callback_data": f"cancel:{order_id}"}],
        ]
    }


# ---------- Routes ----------
@app.route("/", methods=["GET"])
def index():
    return f"{APP_NAME} is running 🚀"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    logger.info("Incoming update: %s", update)

    # ------------- MESSAGE HANDLING -------------
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        # Commands
        if text == "/start":
            text_welcome = (
                f"👋 <b>Welcome to {APP_NAME}</b>\n\n"
                "High-quality AI image & video packs (demo mode)\n\n"
                "Choose an option below:"
            )
            send_message(chat_id, text_welcome, reply_markup=main_menu_keyboard())
            return "ok"

        if text == "/store" or text == "/packs":
            # show all packs
            send_message(chat_id, "<b>Available packs:</b>", reply_markup=packs_keyboard())
            return "ok"

        if text == "/help":
            send_message(chat_id, "Commands:\n/start - welcome\n/store - list packs\n/help - this help")
            return "ok"

        # Fallback: echo or help
        send_message(chat_id, "I did not understand that. Use /start or /help.")
        return "ok"

    # ------------- CALLBACK HANDLING -------------
    if "callback_query" in update:
        q = update["callback_query"]
        cq_id = q["id"]
        data = q.get("data", "")
        from_user = q["from"]
        chat_id = q["message"]["chat"]["id"] if q.get("message") else from_user["id"]
        logger.info("Callback query: %s from %s", data, from_user.get("username"))

        # Always answer callback to remove the "loading" state in client
        answer_callback(cq_id)

        # Main menu navigation
        if data == "menu_images":
            send_message(chat_id, "<b>Image Packs</b>\nChoose a pack:", reply_markup=packs_keyboard(pack_type="image"))
            return "ok"

        if data == "menu_videos":
            send_message(chat_id, "<b>Video Packs</b>\nChoose a pack:", reply_markup=packs_keyboard(pack_type="video"))
            return "ok"

        if data == "menu_demo":
            # Show a generic demo message
            send_message(chat_id, "🎁 <b>Free Demo</b>\nPick a demo from available packs:", reply_markup=packs_keyboard())
            return "ok"

        if data == "menu_about":
            send_message(chat_id, f"ℹ️ <b>About {APP_NAME}</b>\n\nThis bot demonstrates a demo storefront for AI visuals.")
            return "ok"

        if data == "back_main":
            send_message(chat_id, "Back to main menu:", reply_markup=main_menu_keyboard())
            return "ok"

        if data == "back_packs":
            send_message(chat_id, "Packs list:", reply_markup=packs_keyboard())
            return "ok"

        # pack:<id>
        if data.startswith("pack:"):
            pack_id = data.split("pack:", 1)[1]
            pack = PACKS.get(pack_id)
            if not pack:
                send_message(chat_id, "Pack not found.")
                return "ok"
            # show pack details + actions
            text = f"<b>{pack['title']}</b>\n\n{pack['description']}\n\nPrice: <b>{pack['price']}</b>"
            # If demo URL available, send preview
            if pack.get("demo_url"):
                send_photo(chat_id, pack["demo_url"], caption=text, reply_markup=pack_actions_keyboard(pack_id))
            else:send_message(chat_id, text, reply_markup=pack_actions_keyboard(pack_id))
            return "ok"

        # demo:<pack_id> -> send demo media
        if data.startswith("demo:"):
            pack_id = data.split("demo:", 1)[1]
            pack = PACKS.get(pack_id)
            if not pack:
                send_message(chat_id, "Demo not available.")
                return "ok"
            if pack["type"] == "image":
                send_photo(chat_id, pack.get("demo_url", DEFAULT_DEMO_IMAGE), caption=f"Demo: {pack['title']}")
            else:
                # For video demo we'll send a preview image and link text (simplified)
                send_message(chat_id, f"Demo preview for {pack['title']}:\n{pack.get('demo_url', DEFAULT_DEMO_VIDEO)}")
            return "ok"

        # buy:<pack_id> -> create a simulated order
        if data.startswith("buy:"):
            pack_id = data.split("buy:", 1)[1]
            pack = PACKS.get(pack_id)
            if not pack:
                send_message(chat_id, "Pack not found.")
                return "ok"
            # Create a fake order id
            import uuid
            order_id = str(uuid.uuid4())[:8]
            ORDERS[order_id] = {"pack_id": pack_id, "chat_id": chat_id, "status": "pending"}
            send_message(chat_id, f"Order created (simulated). Order ID: <code>{order_id}</code>\nPrice: {pack['price']}",
                         reply_markup=buy_confirm_keyboard(order_id))
            return "ok"

        # paid:<order_id> -> simulate payment complete
        if data.startswith("paid:"):
            order_id = data.split("paid:", 1)[1]
            order = ORDERS.get(order_id)
            if not order:
                send_message(chat_id, "Order not found.")
                return "ok"
            order["status"] = "paid"
            pack = PACKS.get(order["pack_id"])
            # Simulate sending a download link
            download_link = f"https://example.com/downloads/{order_id}/{pack['id']}.zip"
            send_message(chat_id, f"Payment received ✅\nDownload link (simulated):\n{download_link}")
            return "ok"

        # cancel:<order_id>
        if data.startswith("cancel:"):
            order_id = data.split("cancel:", 1)[1]
            order = ORDERS.pop(order_id, None)
            if order:
                send_message(chat_id, f"Order {order_id} cancelled.")
            else:
                send_message(chat_id, "Order not found or already cancelled.")
            return "ok"

        # Unknown callback
        send_message(chat_id, "Unknown action.")
        return "ok"

    # End update handling
    return "ok"


# ---------- Run info ----------
if __name__ == "__main__":
    # Local dev: run with python app.py (not for production)
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN not set; the bot will not be able to send messages.")
    print("APP STARTED 🚀")
    app.run(host="0.0.0.0", port=8000)