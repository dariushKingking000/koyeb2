#!/usr/bin/env python3
"""
Final cleaned Telegram + NowPayments Flask app.

Features:
- Main menu: Image Packs, Video Packs, Demo (rotates daily), About.
- When user taps a pack: show title/description + actions only (no auto demo).
- "Demo Preview" sends the pack's demo media.
- "Buy" creates an order; user sees "Pay with Crypto" (immediately creates invoice) and "Cancel".
- All user-facing text is English.
- Telegram "wrong type of the web page content" handled by downloading and uploading media as a fallback.
- Demo rotation uses the DRIVE_LINKS list below (converts drive share URLs into direct download URLs).
"""

import os
import re
import json
import time
import logging
import threading
import requests
import hmac
import hashlib
from io import BytesIO
from flask import Flask, request, jsonify

from sqlalchemy import create_engine, Column, String, BigInteger, Float, JSON as SA_JSON
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------- Configuration ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None

NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://example.com")

APP_NAME = "Mythic AI Store"

DEFAULT_DEMO_IMAGE = "https://via.placeholder.com/1024x768.png?text=Demo+Image"
DEFAULT_DEMO_VIDEO = "https://via.placeholder.com/1280x720.png?text=Demo+Video"

# ---------------- Catalog / Prices ----------------
PRICES = {
    "face_pack": 10.0,
    "love_pack": 10.0,
    "planets_pack": 10.0,
    "video1": 5.0,
    "video2": 5.0,
    "video3": 5.0,
}

PACKS = {
    "face_pack": {
        "id": "face_pack",
        "title": "Face Pack",
        "description": "AI Faces Collection",
        "type": "image",
        "demo_url": "https://drive.google.com/uc?export=download&id=1BLOOQgUDGlsrz_gNS0z9aCcHdtD1L_-0",
        "deliver_url": "https://drive.google.com/uc?export=download&id=1FY77eK4EIWMYP3UT37dP_q1Jt9smdPqx",
    },
    "love_pack": {
        "id": "love_pack",
        "title": "Love Pack",
        "description": "Romantic AI Images",
        "type": "image",
        "demo_url": "https://drive.google.com/uc?export=download&id=1BLOOQgUDGlsrz_gNS0z9aCcHdtD1L_-0",
        "deliver_url": "https://drive.google.com/uc?export=download&id=1vtYcZmq5QHAJSlCnUutneAllL75Kxfbw",
    },
    "planets_pack": {
        "id": "planets_pack",
        "title": "Planets Pack",
        "description": "AI Generated Planets",
        "type": "image",
        "demo_url": "https://drive.google.com/uc?export=download&id=1BLOOQgUDGlsrz_gNS0z9aCcHdtD1L_-0",
        "deliver_url": "https://drive.google.com/uc?export=download&id=108HXs4tBjXRRm5z2To6VQthW6HtLIeyO",
    },
    "video1": {
        "id": "video1",
        "title": "Love Video",
        "description": "Romantic cinematic AI video",
        "type": "video",
        "demo_url": "https://drive.google.com/uc?export=download&id=1ZrAjxl-iwc_0sKUi1UHqu_NPSY3Xts5B",
        "deliver_url": "https://drive.google.com/uc?export=download&id=1Yc3mFUTAJ0Dnch5ZQxHLgK8Rza1zowlc",
    },
    "video2": {
        "id": "video2",
        "title": "Alone Human Video",
        "description": "Emotional AI cinematic scene",
        "type": "video",
        "demo_url": "https://drive.google.com/uc?export=download&id=1ZrAjxl-iwc_0sKUi1UHqu_NPSY3Xts5B",
        "deliver_url": "https://drive.google.com/uc?export=download&id=1cbXn5BvCe-pCwWNCYv0xWVv6ndnGUcr3",
    },
    "video3": {
        "id": "video3",
        "title": "Planet Video",
        "description": "Epic AI space cinematic video",
        "type": "video",
        "demo_url": "https://drive.google.com/uc?export=download&id=1ZrAjxl-iwc_0sKUi1UHqu_NPSY3Xts5B",
        "deliver_url": "https://drive.google.com/uc?export=download&id=1OmvHHlB-eYsIYV9XEES15B6fScMyEe3d",
    },
}

# ---------------- Demo rotation links (user-provided) ----------------
# The user provided a list of Google Drive view links; convert to direct download if possible.
DRIVE_LINKS = [
    "https://drive.google.com/file/d/1Z1pJljlqiSwv50gzfMMObm6O9sEdnvf-/view?usp=drivesdk",
    "https://drive.google.com/file/d/18V8UEIg4CZ-ZOh60OzL464a_ejJu9O15/view?usp=drivesdk",
    "https://drive.google.com/file/d/1nKiuDFLIV2eH9I1bvFsM7I-m8aQlVS8b/view?usp=drivesdk",
    "https://drive.google.com/file/d/1AnC8oa0yagOsSLQzKMj6F6dI9F-vVjAm/view?usp=drivesdk",
    "https://drive.google.com/file/d/1A6iepbWwsgO0j5dcJXjyaAzuHV0pbBcZ/view?usp=drivesdk",
    "https://drive.google.com/file/d/1NcXQG8QaMmiFmHKYtqcVAmBvWN-NWOBJ/view?usp=drivesdk",
    "https://drive.google.com/file/d/1dQSD9wh-DDStuMksXLs-UkTH6X1dn_r1/view?usp=drivesdk",
    "https://drive.google.com/file/d/1nzThkEqpE4r2op9RQxodZn34ICGcWSNu/view?usp=drivesdk",
    "https://drive.google.com/file/d/1CvfO009_kAgvK147-kbVbzmGW4cLHnxo/view?usp=drivesdk",
    "https://drive.google.com/file/d/1K8rYumafJFPnTGU9JlwWY_udjWBYNDe0/view?usp=drivesdk",
    "https://drive.google.com/file/d/1lEQI46H_RsXNPj3lrLFrruRbSfWAI3nk/view?usp=drivesdk",
    "https://drive.google.com/file/d/1ViTDUK9Hj-e3r4g0sW-LB3rX0N3fDq0N/view?usp=drivesdk",
    "https://drive.google.com/file/d/1b7BMbcDF3m_EpXohO-egYqNXzx21AI7G/view?usp=drivesdk",
    "https://drive.google.com/file/d/1-gdYEM-Rs2I7WpXXGFCzlxldIKcY49J6/view?usp=drivesdk",
    "https://drive.google.com/file/d/1cpA9pDIBpXCYC1lWha63q8x0VaPGSs6M/view?usp=drivesdk",
    "https://drive.google.com/file/d/1b9p1TPrRwLHFJV42_FcEfFoke_aClomH/view?usp=drivesdk",
]

def drive_view_to_download(url: str) -> str:
    """Convert common Google Drive 'view' link to direct download (uc?export=download&id=...)."""
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url)
    if m:
        file_id = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

DEMO_MEDIA = [drive_view_to_download(u) for u in DRIVE_LINKS if u]

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mythic-bot")

# ---------------- Flask ----------------
app = Flask(__name__)

# ---------------- Database (SQLAlchemy) ----------------
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("Postgres.DATABASE_URL") or os.getenv("Postgres.DATABASE")
if not DATABASE_URL:
    DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite:///local.db")
    logger.warning("DATABASE_URL is not set. Falling back to local sqlite (development only).")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(String, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    product_id = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USDT")
    status = Column(String, nullable=False, default="pending")
    invoice = Column(SA_JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)  # epoch seconds
    paid_at = Column(BigInteger, nullable=True)
    tx_info = Column(SA_JSON, nullable=True)

Base.metadata.create_all(bind=engine)

# ---------------- Telegram helpers ----------------
def telegram_request_json(method: str, payload: dict, timeout=20):
    if not API_URL:
        logger.error("BOT_TOKEN is not set")
        return None
    url = f"{API_URL}/{method}"
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        if r.status_code != 200:
            logger.warning("Telegram API returned %s: %s", r.status_code, r.text)
        try:
            return r.json()
        except Exception:
            return {"ok": False, "error": "invalid_json_response", "status_code": r.status_code, "text": r.text}
    except Exception as e:
        logger.exception("Telegram request failed: %s", e)
        return None

def telegram_request_multipart(method: str, data: dict, files: dict, timeout=60):
    if not API_URL:
        logger.error("BOT_TOKEN is not set")
        return None
    url = f"{API_URL}/{method}"
    try:
        r = requests.post(url, data=data, files=files, timeout=timeout)
        if r.status_code != 200:
            logger.warning("Telegram multipart API returned %s: %s", r.status_code, r.text)
        try:
            return r.json()
        except Exception:
            return {"ok": False, "error": "invalid_json_response", "status_code": r.status_code, "text": r.text}
    except Exception as e:
        logger.exception("Telegram multipart request failed: %s", e)
        return None

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    return telegram_request_json("sendMessage", payload)

def send_photo(chat_id, photo_url, caption=None, reply_markup=None):
    payload = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    resp = telegram_request_json("sendPhoto", payload)
    if resp and not resp.get("ok"):
        desc = (resp.get("description") or "").lower()
        if "wrong type of the web page content" in desc or "web page" in desc:
            try:
                r = requests.get(photo_url, timeout=20)
                r.raise_for_status()
                content = r.content
                ctype = r.headers.get("Content-Type", "") or "image/jpeg"
                files = {"photo": ("photo.jpg", BytesIO(content), ctype)}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption
                    data["parse_mode"] = "HTML"
                return telegram_request_multipart("sendPhoto", data, files)
            except Exception:
                logger.exception("Failed to download/upload photo fallback")
                return send_message(chat_id, (caption or "") + "\n\n" + photo_url, reply_markup=reply_markup)
    return resp

def send_video(chat_id, video_url, caption=None, reply_markup=None):
    payload = {"chat_id": chat_id, "video": video_url}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    resp = telegram_request_json("sendVideo", payload)
    if resp and not resp.get("ok"):
        desc = (resp.get("description") or "").lower()
        if "wrong type of the web page content" in desc or "web page" in desc:
            try:
                r = requests.get(video_url, timeout=30, stream=True)
                r.raise_for_status()
                content_length = int(r.headers.get("Content-Length") or 0)
                max_size = 50 * 1024 * 1024  # 50 MB
                if content_length and content_length > max_size:
                    return send_message(chat_id, (caption or "") + "\n\n" + video_url, reply_markup=reply_markup)
                content = r.content
                ctype = r.headers.get("Content-Type", "") or "video/mp4"
                files = {"video": ("video.mp4", BytesIO(content), ctype)}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption
                    data["parse_mode"] = "HTML"
                return telegram_request_multipart("sendVideo", data, files)
            except Exception:
                logger.exception("Failed to download/upload video fallback")
                return send_message(chat_id, (caption or "") + "\n\n" + video_url, reply_markup=reply_markup)
    return resp

def send_document(chat_id, doc_url, caption=None, reply_markup=None):
    payload = {"chat_id": chat_id, "document": doc_url}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    resp = telegram_request_json("sendDocument", payload)
    if resp and not resp.get("ok"):
        desc = (resp.get("description") or "").lower()
        if "wrong type of the web page content" in desc:
            try:
                r = requests.get(doc_url, timeout=30)
                r.raise_for_status()
                content = r.content
                ctype = r.headers.get("Content-Type", "") or "application/octet-stream"
                files = {"document": ("file", BytesIO(content), ctype)}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption
                    data["parse_mode"] = "HTML"
                return telegram_request_multipart("sendDocument", data, files)
            except Exception:
                logger.exception("Failed to download/upload document fallback")
                return send_message(chat_id, (caption or "") + "\n\n" + doc_url, reply_markup=reply_markup)
    return resp

def answer_callback(cq_id):
    telegram_request_json("answerCallbackQuery", {"callback_query_id": cq_id})

# ---------------- Keyboards ----------------
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
            [{"text": "🛒 Buy", "callback_data": f"buy:{pack_id}"}],
            [{"text": "🔙 Back", "callback_data": "back"}],
        ]
    }

def payment_select_for_order(order_id):
    return {
        "inline_keyboard": [
            [{"text": "💰 Pay with Crypto", "callback_data": f"pay_now:{order_id}"}],
            [{"text": "❌ Cancel", "callback_data": f"cancel:{order_id}"}],
        ]
    }

def invoice_kb(order_id):
    return {
        "inline_keyboard": [
            [{"text": "✅ I Paid (check)", "callback_data": f"check_paid:{order_id}"}],
            [{"text": "🔁 Retry / New Invoice", "callback_data": f"retry:{order_id}"}],
        ]
    }

# ---------------- Utilities (DB) ----------------
def generate_order_id():
    return f"ORD{int(time.time() * 1000)}"

def create_order_db(user_id, pack_id):
    session = SessionLocal()
    try:
        order_id = generate_order_id()
        price = float(PRICES.get(pack_id, 1.0))
        created_at = int(time.time())
        o = Order(
            order_id=order_id,
            user_id=int(user_id),
            product_id=pack_id,
            price=price,
            currency="USDT",
            status="pending",
            invoice=None,
            created_at=created_at,
            paid_at=None,
            tx_info=None,
        )
        session.add(o)
        session.commit()
        session.refresh(o)
        return {
            "order_id": o.order_id,
            "user_id": o.user_id,
            "product_id": o.product_id,
            "price": o.price,
            "currency": o.currency,
            "status": o.status,
            "created_at": o.created_at,
            "invoice": o.invoice,
        }
    except Exception:
        session.rollback()
        logger.exception("Failed to create order in DB")
        raise
    finally:
        session.close()

def get_order_db(order_id):
    session = SessionLocal()
    try:
        o = session.query(Order).filter_by(order_id=order_id).first()
        if not o:
            return None
        return {
            "order_id": o.order_id,
            "user_id": o.user_id,
            "product_id": o.product_id,
            "price": o.price,
            "currency": o.currency,
            "status": o.status,
            "invoice": o.invoice,
            "created_at": o.created_at,
            "paid_at": o.paid_at,
            "tx_info": o.tx_info,
        }
    finally:
        session.close()

def list_user_orders_db(user_id):
    session = SessionLocal()
    try:
        rows = session.query(Order).filter_by(user_id=int(user_id)).order_by(Order.created_at.desc()).all()
        res = []
        for o in rows:
            res.append({
                "order_id": o.order_id,
                "product_id": o.product_id,
                "price": o.price,
                "currency": o.currency,
                "status": o.status,
                "created_at": o.created_at,
                "paid_at": o.paid_at
            })
        return res
    finally:
        session.close()

def update_order_invoice_db(order_id, invoice_obj):
    session = SessionLocal()
    try:
        o = session.query(Order).filter_by(order_id=order_id).first()
        if not o:
            return None
        o.invoice = invoice_obj
        session.commit()
        return True
    except Exception:
        session.rollback()
        logger.exception("Failed to update invoice")
        return False
    finally:
        session.close()

def mark_order_paid_db(order_id, tx_info=None):
    session = SessionLocal()
    try:
        o = session.query(Order).filter_by(order_id=order_id).first()
        if not o:
            return False
        o.status = "paid"
        o.paid_at = int(time.time())
        o.tx_info = tx_info
        session.commit()
        # deliver file to user (attempt)
        try:
            chat_id = o.user_id
            product = PACKS.get(o.product_id)
            if product:
                send_document(chat_id, product.get("deliver_url"), caption=f"Here is your pack: {product.get('title')}")
            else:
                send_message(chat_id, "✅ Payment confirmed. Your file is ready.")
        except Exception:
            logger.exception("Failed to deliver file after marking paid")
        return True
    except Exception:
        session.rollback()
        logger.exception("Failed to mark order paid")
        return False
    finally:
        session.close()

# ---------------- NowPayments integration ----------------
def create_invoice_nowpayments_db(order):
    if not NOWPAYMENTS_API_KEY:
        fake = {
            "id": f"fake-inv-{order['order_id']}",
            "pay_url": f"{PUBLIC_URL}/pay/{order['order_id']}",
            "status": "waiting",
            "price_amount": order["price"],
            "price_currency": order["currency"],
        }
        update_order_invoice_db(order["order_id"], fake)
        return fake

    url = "https://api.nowpayments.io/v1/invoice"
    headers = {"x-api-key": NOWPAYMENTS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "price_amount": order["price"],
        "price_currency": order["currency"],
        "order_id": order["order_id"],
        "order_description": f"{APP_NAME} - {order['product_id']}",
        "ipn_callback_url": f"{PUBLIC_URL}/nowpayments_webhook",
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        update_order_invoice_db(order["order_id"], data)
        return data
    except Exception:
        logger.exception("NowPayments invoice creation failed")
        fake = {
            "id": f"fallback-inv-{order['order_id']}",
            "pay_url": f"{PUBLIC_URL}/pay/{order['order_id']}",
            "status": "waiting",
            "price_amount": order["price"],
            "price_currency": order["currency"],
        }
        update_order_invoice_db(order["order_id"], fake)
        return fake

# ---------------- Demo selection ----------------
def get_demo_media_for_today():
    """Return one demo media (rotating daily) from DEMO_MEDIA list."""
    if not DEMO_MEDIA:
        return None
    idx = (int(time.time()) // 86400) % len(DEMO_MEDIA)
    return DEMO_MEDIA[idx]

# ---------------- Core Logic ----------------
def handle_update(update):
    try:
        # plain message
        if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")

            if text == "/start":
                send_message(chat_id, f"👋 <b>Welcome to {APP_NAME}</b>\nChoose:", reply_markup=main_menu())
                return

            if text and text.lower().strip() == "orders":
                user_orders = list_user_orders_db(chat_id)
                if not user_orders:
                    send_message(chat_id, "You have no orders yet.")
                else:
                    txt = "Your orders:\n\n"
                    for o in user_orders:
                        txt += f"{o['order_id']} - {o['product_id']} - {o['price']} {o['currency']} - {o['status']}\n"
                    send_message(chat_id, txt)
                return

        # callback queries (inline buttons)
        if "callback_query" in update:
            q = update["callback_query"]
            data = q.get("data", "")
            # some clients may not include message (e.g. old callbacks); guard
            chat_id = None
            if q.get("message"):
                chat_id = q["message"]["chat"]["id"]
            cq_id = q.get("id")

            # reply to callback immediately
            if cq_id:
                answer_callback(cq_id)

            if not chat_id:
                logger.warning("Callback without message (no chat_id); ignoring.")
                return

            if data == "images":
                send_message(chat_id, "🖼 Image Packs:", reply_markup=packs_keyboard("image"))
                return
            if data == "videos":
                send_message(chat_id, "🎥 Video Packs:", reply_markup=packs_keyboard("video"))
                return
            if data == "demo":
                media = get_demo_media_for_today()
                if not media:
                    send_message(chat_id, "No demo available.")
                    return
                # try detect video vs image by extension/content-type guess
                if any(media.lower().endswith(ext) for ext in (".mp4", ".mov", ".webm")) or "video" in media:
                    send_video(chat_id, media, "🎁 Demo")
                else:
                    send_photo(chat_id, media, "🎁 Demo")
                return
            if data == "about":
                send_message(chat_id, "🤖 Mythic AI Store\nAI-generated image & video packs.")
                return
            if data == "back":
                send_message(chat_id, "Main menu:", reply_markup=main_menu())
                return

            # pack -> show title/description + actions only
            if data.startswith("pack:"):
                pid = data.split(":", 1)[1]
                p = PACKS.get(pid)
                if p:
                    caption = f"<b>{p['title']}</b>\n{p['description']}"
                    send_message(chat_id, caption, reply_markup=pack_actions(pid))
                else:
                    send_message(chat_id, "Pack not found.")
                return

            # demo preview for pack (explicit)
            if data.startswith("demo_pack:"):
                pid = data.split(":", 1)[1]
                p = PACKS.get(pid)
                if not p:
                    send_message(chat_id, "Pack not found.")
                    return
                if p.get("type") == "video":
                    send_video(chat_id, p.get("demo_url") or DEFAULT_DEMO_VIDEO, "📤 Demo preview")
                else:
                    send_photo(chat_id, p.get("demo_url") or DEFAULT_DEMO_IMAGE, "📤 Demo preview")
                return

            # buy -> create order (pack_id passed)
            if data.startswith("buy:"):
                pid = data.split(":", 1)[1]
                if pid not in PACKS:
                    send_message(chat_id, "Product not found.")
                    return
                order = create_order_db(chat_id, pid)
                send_message(
                    chat_id,
                    f"🧾 Order created: <b>{order['order_id']}</b>\nProduct: {pid}\nPrice: {order['price']} {order['currency']}\n\nChoose payment method:",
                    reply_markup=payment_select_for_order(order["order_id"])
                )
                return

            # cancel: normally contains order_id
            if data.startswith("cancel:"):
                oid = data.split(":", 1)[1]
                o = get_order_db(oid)
                if o and o["user_id"] == chat_id:
                    session = SessionLocal()
                    try:
                        dbo = session.query(Order).filter_by(order_id=oid).first()
                        if dbo and dbo.status == "pending":
                            dbo.status = "cancelled"
                            session.commit()
                            send_message(chat_id, f"Order {oid} cancelled.")
                        else:
                            send_message(chat_id, "Order not found or cannot cancel.")
                    finally:
                        session.close()
                else:
                    # if cancel isn't an order id, just return to main menu
                    send_message(chat_id, "Returning to main menu.", reply_markup=main_menu())
                return

            # pay_now: order_id -> immediately create invoice and return pay_url
            if data.startswith("pay_now:"):
                oid = data.split(":", 1)[1]
                order = get_order_db(oid)
                if not order:
                    send_message(chat_id, "Order not found.")
                    return
                invoice = create_invoice_nowpayments_db(order)
                pay_url = invoice.get("pay_url") or invoice.get("invoice_url") or invoice.get("url") or f"{PUBLIC_URL}/pay/{oid}"
                send_message(
                    chat_id,
                    f"Invoice created.\n\nPay here: {pay_url}\n\nAfter payment press <b>I Paid (check)</b>.",
                    reply_markup=invoice_kb(oid)
                )
                return

            # retry invoice
            if data.startswith("retry:"):
                oid = data.split(":", 1)[1]
                order = get_order_db(oid)
                if not order:
                    send_message(chat_id, "Order not found.")
                    return
                invoice = create_invoice_nowpayments_db(order)
                pay_url = invoice.get("pay_url") or invoice.get("invoice_url") or invoice.get("url") or f"{PUBLIC_URL}/pay/{oid}"
                send_message(chat_id, f"New invoice: {pay_url}", reply_markup=invoice_kb(oid))
                return

            # check paid
            if data.startswith("check_paid:"):
                oid = data.split(":", 1)[1]
                o = get_order_db(oid)
                if not o:
                    send_message(chat_id, "Order not found.")
                    return
                invoice = o.get("invoice") or {}
                if o["status"] == "paid" or (isinstance(invoice, dict) and invoice.get("status") == "paid"):
                    mark_order_paid_db(oid, tx_info=invoice)
                    send_message(chat_id, f"Order {oid} is already paid and delivered.")
                else:
                    send_message(chat_id, "Payment not detected yet. Please wait a few minutes and try again.")
                return

    except Exception:
        logger.exception("handle_update failed")

# ---------------- Routes ----------------
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

@app.route("/nowpayments_webhook", methods=["POST"])
def nowpayments_webhook():
    try:
        data = request.get_json(force=True)
    except Exception:
        logger.exception("Invalid JSON in webhook")
        return jsonify({"ok": False}), 400

    logger.info("NowPayments webhook received: %s", data)
    received_sig = request.headers.get("x-nowpayments-sig")
    if NOWPAYMENTS_IPN_SECRET and received_sig:
        sorted_json = json.dumps(data, separators=(',', ':'), sort_keys=True)
        generated_sig = hmac.new(NOWPAYMENTS_IPN_SECRET.encode(), sorted_json.encode(), hashlib.sha512).hexdigest()
        if generated_sig != received_sig:
            logger.warning("Invalid NOWPayments signature")
            return jsonify({"ok": False, "reason": "invalid_signature"}), 403

    order_id = data.get("order_id") or data.get("orderId") or (data.get("invoice") or {}).get("order_id") or data.get("purchase_id")
    status = data.get("status") or data.get("payment_status") or (data.get("invoice") or {}).get("status")
    if not order_id:
        logger.warning("No order_id in webhook payload")
        return jsonify({"ok": False, "reason": "no_order_id"}), 400

    if str(status).lower() in ("finished", "paid", "success", "confirmed"):
        o = get_order_db(order_id)
        if o:
            pay_amount = data.get("price_amount") or data.get("pay_amount") or (data.get("invoice") or {}).get("price_amount")
            try:
                if pay_amount is not None and float(pay_amount) < float(o["price"]) * 0.99:
                    logger.warning("Paid amount %s less than expected %s for order %s", pay_amount, o["price"], order_id)
            except Exception:
                pass
        mark_order_paid_db(order_id, tx_info=data)
        return jsonify({"ok": True}), 200
    else:
        update_order_invoice_db(order_id, {"status": status})
        return jsonify({"ok": True, "status": status}), 200

# Simple local fake pay page (development)
@app.route("/pay/<order_id>")
def pay_page(order_id):
    o = get_order_db(order_id)
    if not o:
        return "Order not found", 404
    html = f"""
    <html><body>
      <h3>Fake pay page for order {order_id}</h3>
      <p>Amount: {o['price']} {o['currency']}</p>
      <form action="/pay_simulate/{order_id}" method="post">
        <button type="submit">Simulate payment (mark as paid)</button>
      </form>
    </body></html>
    """
    return html

@app.route("/pay_simulate/<order_id>", methods=["POST"])
def pay_simulate(order_id):
    o = get_order_db(order_id)
    if not o:
        return "Order not found", 404
    payload = {"order_id": order_id, "status": "finished", "invoice_id": f"sim-{order_id}"}
    mark_order_paid_db(order_id, tx_info=payload)
    return f"Order {order_id} marked as paid (simulated). You can return to Telegram."

# ---------------- Run ----------------
if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is NOT set. Telegram messages will fail.")
    if not NOWPAYMENTS_API_KEY:
        logger.warning("NOWPAYMENTS_API_KEY is NOT set. Invoices will be simulated.")
    logger.info("Starting %s ...", APP_NAME)
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)