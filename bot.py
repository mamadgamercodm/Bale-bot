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

MATCHES = {
    "اسپانیا vs عربستان": jdatetime.datetime(1405, 3, 31, 19, 30),
    "بلژیک vs ایران": jdatetime.datetime(1405, 3, 31, 22, 30),
    "کیپ ورد vs اروگویه": jdatetime.datetime(1405, 4, 1, 1, 30),
    "مصر vs نیوزلند": jdatetime.datetime(1405, 4, 1, 4, 0)
}

GAME_BALLS = {
    "اسپانیا vs عربستان": "🔵",
   "بلژیک vs ایران": "🟢",
   "کیپ ورد vs اروگویه": "🔴",
   "مصر vs نیوزلند": "🟡"
}

def normalize_str(text):
    return "".join(text.replace('ي', 'ی').replace('ك', 'ک').replace("‌", "").split()).lower()

def match_game(input_text):
    for m in MATCHES:
        parts = re.split(r'\s*(?:vs|v\.s|v\s*s|-|–|—)\s*', m, flags=re.IGNORECASE)
        if all(normalize_str(p) in normalize_str(input_text) for p in parts if p.strip()):
            return m
    return None

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {m: [] for m in MATCHES}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_message(chat_id, text):
    requests.post(API_URL + "sendMessage", json={"chat_id": chat_id, "text": text})

def process_update(update):
    if 'message' not in update or 'text' not in update['message']: return
    
    msg_text = update['message']['text'].strip()
    chat_id = update['message']['chat']['id']
    user_name = update['message']['from'].get('first_name', 'کاربر')

    # دستور نمایش
    if msg_text == "/show":
        data = load_data()
        summary = f"📋 {TITLE}\n\n"
        for m, time in MATCHES.items():
            is_locked = jdatetime.datetime.now() > time
            ball = "🔴" if is_locked else GAME_BALLS.get(m, "⚪")
            preds = data.get(m, [])
            summary += f"{ball} {m}\n"
            if not preds:
                summary += "   └ 🔮 هنوز پیش‌بینی نشده\n"
            else:
                for p in preds:
                    summary += f"   └ {p['user']}: {p['pred']}\n"
            summary += "\n"
        send_message(chat_id, summary)
        return

    # تشخیص بازی در خط اول
    lines = msg_text.split('\n')
    matched_match = match_game(lines[0])
    
    if matched_match:
        # چک کردن زمان
        if jdatetime.datetime.now() > MATCHES[matched_match]:
            # ارسال لیست وضعیت در صورت قفل بودن
            data = load_data()
            msg = f"🔴 بازی {matched_match} قفل شد:\n"
            for p in data.get(matched_match, []):
                msg += f"- {p['user']}: {p['pred']}\n"
            send_message(chat_id, msg)
            return

        # ثبت پیش‌بینی
        if len(lines) > 1 and lines[1].strip():
            pred = lines[1].strip()
            data = load_data()
            if len(data[matched_match]) < 40:
                data[matched_match].append({"user": user_name, "pred": pred})
                save_data(data)
                send_message(chat_id, f"{GAME_BALLS.get(matched_match, '✅')} پیش‌بینی شما ثبت شد.")
            else:
                send_message(chat_id, "❌ ظرفیت پیش‌بینی برای این بازی تکمیل شده است.")
        return

@app.route('/webhook', methods=['POST'])
def webhook():
    process_update(request.get_json())
    return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
