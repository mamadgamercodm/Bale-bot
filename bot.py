import os
import json
import re
import requests
import jdatetime
from flask import Flask, request

# --- تنظیمات ---
TOKEN = os.getenv("TOKEN", "838006855:bDxGlcHGdhvR8GxFfBaosYyZjOruZ0RFlfw")
API_URL = f"https://tapi.bale.ai/bot{TOKEN}/"
DATA_FILE = "data.json"
TITLE = "WORLDCUP PREDICTION 69"

app = Flask(__name__)

# --- لیست مسابقات ---
MATCHES = {
    "استراليا vs آمريکا": jdatetime.datetime(1405, 3, 29, 22, 30),
    "مراکش vs اسکاتلند": jdatetime.datetime(1405, 3, 30, 1, 30),
    "هاييتي vs برزيل": jdatetime.datetime(1405, 3, 30, 4, 0),
    "پاراگوئه vs ترکيه": jdatetime.datetime(1405, 3, 30, 6, 30)
}

GAME_BALLS = {
    "استراليا vs آمريکا": "🔵",
    "مراکش vs اسکاتلند": "🟢",
    "هاييتي vs برزيل": "🔴",
    "پاراگوئه vs ترکيه": "🟡"
}

# --- توابع ---
def normalize_str(text):
    text = text.replace('ي', 'ی').replace('ك', 'ک').replace("‌", "")
    return "".join(text.split()).lower()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_message(chat_id, text):
    requests.post(API_URL + "sendMessage", json={"chat_id": chat_id, "text": text})

def process_update(update):
    msg = update.get('message', {})
    if 'text' not in msg: return
    
    chat_id = msg['chat']['id']
    text = msg['text'].strip()
    user_name = msg.get('from', {}).get('username') or msg.get('from', {}).get('first_name', 'کاربر')

    if text == "/show":
        data = load_data()
        summary = f"📋 {TITLE}\n\n"
        for match in MATCHES:
            ball = GAME_BALLS.get(match, "⚪")
            preds = data.get(match, [])
            summary += f"{ball} {match}:\n"
            if not preds: summary += "   └ 🔮 هنوز پیش‌بینی نشده\n"
            for p in preds:
                summary += f"   └ 👤 {p['user']}: {p['pred']}\n"
            summary += "\n"
        send_message(chat_id, summary)
        return

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 2: return

    # تشخیص بازی
    matched_match = None
    for m in MATCHES:
        if normalize_str(lines[0]) in normalize_str(m):
            matched_match = m
            break
    
    if not matched_match: return

    # بررسی زمان
    if jdatetime.datetime.now() > MATCHES[matched_match]:
        send_message(chat_id, f"❌ زمان پیش‌بینی {matched_match} تمام شده.")
        return

    # ذخیره پیش‌بینی‌ها
    data = load_data()
    if matched_match not in data: data[matched_match] = []
    
    new_predictions = lines[1:]
    for p in new_predictions:
        data[matched_match].append({"user": user_name, "pred": p})
    
    save_data(data)
    send_message(chat_id, f"✅ {len(new_predictions)} پیش‌بینی برای {matched_match} ثبت شد.")

@app.route('/webhook', methods=['POST'])
def webhook():
    process_update(request.get_json())
    return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

