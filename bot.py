import os
import json
import time
import requests
import jdatetime
from flask import Flask, request

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("TOKEN", "توکنم")
API_URL = f"https://tapi.bale.ai/bot{TOKEN}/"
DATA_FILE = "data.json"
TITLE = "WORLDCUP PREDICTION 69"

app = Flask(__name__)

# =====================
# MATCHES
# =====================
MATCHES = {
    "آفریقا جنوبی vs جمهوری چک": "1403/09/28",
    "بوسنی vs سوییس": "1403/09/28",
    "کانادا vs قطر": "1403/09/28",
    "مکزیک vs کره جنوبی": "1403/09/28",
}

# توپ رنگی اختصاصی هر بازی
GAME_BALLS = {
    "آفریقا جنوبی vs جمهوری چک": "🔵",
    "بوسنی vs سوییس": "🟢",
    "کانادا vs قطر": "🔴",
    "مکزیک vs کره جنوبی": "🟡",
}

# =====================
# HELPERS
# =====================
def normalize_str(s):
    if not s:
        return ""
    return str(s).replace("ك", "ک").replace("ي", "ی").replace("ى", "ی").strip()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_message(chat_id, text):
    try:
        requests.post(
            API_URL + "sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print("send_message error:", e)

def format_predictions_summary(data):
    if TITLE not in data:
        return "هنوز هیچ پیش‌بینی ثبت نشده است."

    summary = f"📊 گزارش پیش‌بینی‌ها برای {TITLE}\n\n"

    for game_name in MATCHES.keys():
        ball = GAME_BALLS.get(game_name, "🟣")
        summary += f"{ball} {game_name}\n"

        preds = data[TITLE].get(game_name, [])
        if not preds:
            summary += "هنوز پیش‌بینی‌ای ثبت نشده.\n\n"
            continue

        for i, p in enumerate(preds, 1):
            result = p.get("result", "نامشخص")
            username = p.get("username", "ناشناس")
            summary += f"{i}) @{username} ➜ {result}\n"
        summary += "\n"

    return summary

def process_update(update):
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    if not text:
        return

    data = load_data()
    if TITLE not in data:
        data[TITLE] = {}

    # /show
    if text == "/show":
        summary = format_predictions_summary(data)
        send_message(chat_id, summary)
        return

    # ذخیره پیش‌بینی
    lines = text.splitlines()
    if len(lines) >= 2:
        game_input = normalize_str(lines[0])
        prediction = lines[1].strip()

        found_game = next(
            (g for g in MATCHES.keys() if normalize_str(g) == game_input),
            None
        )

        if not found_game:
            send_message(chat_id, "نام بازی را درست وارد نکردی.")
            return

        if found_game not in data[TITLE]:
            data[TITLE][found_game] = []

        username = msg.get("from", {}).get("username", "ناشناس")

        data[TITLE][found_game].append({
            "result": prediction,
            "username": username,
            "chat_id": chat_id,
            "timestamp": int(time.time())
        })

        save_data(data)

        send_message(chat_id, f"پیش‌بینی برای «{found_game}» ذخیره شد ✅")
        send_message(chat_id, format_predictions_summary(data))
        return

    send_message(chat_id, "فرمت پیام درست نیست.\n\nنمونه:\nآفریقا جنوبی vs جمهوری چک\n1-0")

# =====================
# WEBHOOK ROUTES
# =====================
@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if update:
        try:
            process_update(update)
        except Exception as e:
            print("Webhook error:", e)
    return "ok", 200

# =====================
# RUN
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
