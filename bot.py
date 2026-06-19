import os
import json
import requests
import jdatetime
from flask import Flask, request

# --- تنظیمات ---
TOKEN = os.getenv("TOKEN", "838006855:bDxGlcHGdhvR8GxFfBaosYyZjOruZ0RFlfw")
API_URL = f"https://tapi.bale.ai/bot{TOKEN}/"
DATA_FILE = "data.json"
TITLE = "WORLDCUP PREDICTION 69"

app = Flask(__name__)

# --- لیست مسابقات به همراه زمان قفل (ساعتِ بازی) ---
# فرمت: "نام بازی": jdatetime.datetime(سال, ماه, روز, ساعت, دقیقه)
MATCHES = {
    "آفریقا جنوبی vs جمهوری چک": jdatetime.datetime(1403, 9, 28, 14, 0),
    "بوسنی vs سوییس": jdatetime.datetime(1403, 9, 28, 16, 0),
    "کانادا vs قطر": jdatetime.datetime(1403, 9, 28, 18, 0),
    "مکزیک vs کره جنوبی": jdatetime.datetime(1403, 9, 28, 20, 0)
}

GAME_BALLS = {
    "آفریقا جنوبی vs جمهوری چک": "🔵",
    "بوسنی vs سوییس": "🟢",
    "کانادا vs قطر": "🔴",
    "مکزیک vs کره جنوبی": "🟡"
}

# --- توابع کمکی ---
def normalize_str(text):
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
    url = API_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def process_update(update):
    if 'message' not in update or 'text' not in update['message']:
        return

    msg_text = update['message']['text'].strip()
    chat_id = update['message']['chat']['id']

    # ۱. پردازش دستور /show (فقط این دستور پاسخ داده می‌شود)
    if msg_text == "/show":
        data = load_data()
        summary = f"📋 *{TITLE}*\n\n"
        for match in MATCHES:
            ball = GAME_BALLS.get(match, "⚪")
            prediction = data.get(match, "ثبت نشده")
            summary += f"{ball} *{match}*\n   └ 🔮 {prediction}\n\n"
        send_message(chat_id, summary)
        return

    # ۲. تشخیص اینکه آیا کاربر قصد پیش‌بینی دارد؟
    # فقط اگر نام بازی در خط اول باشد، ربات وارد فاز پاسخ‌دهی می‌شود
    lines = msg_text.split('\n')
    match_input = lines[0].strip()
    
    matched_match = None
    for m in MATCHES:
        if normalize_str(match_input) == normalize_str(m):
            matched_match = m
            break

    # اگر بازی پیدا نشد، ربات نباید هیچ جوابی بدهد (ساکت می‌ماند)
    if not matched_match:
        return 

    # ۳. حالا که بازی پیدا شد، پاسخ‌های مربوط به پیش‌بینی را می‌دهیم
    if jdatetime.datetime.now() > MATCHES[matched_match]:
        send_message(chat_id, f"❌ متأسفم، زمان پیش‌بینی برای بازی *{matched_match}* تمام شده است.")
    elif len(lines) >= 2:
        prediction_input = lines[1].strip()
        data = load_data()
        data[matched_match] = prediction_input
        save_data(data)
        send_message(chat_id, f"{GAME_BALLS.get(matched_match, '✅')} پیش‌بینی شما ثبت شد.")
    else:
        # اگر نام بازی را درست نوشته ولی خط دوم را ننوشته (راهنمایی می‌کنیم)
        send_message(chat_id, "لطفاً در خط دوم پیش‌بینی خود را بنویسید.")


@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update:
        process_update(update)
    return 'ok', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
