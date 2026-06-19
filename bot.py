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

# --- لیست مسابقات به همراه زمان قفل (ساعتِ بازی) ---
# فرمت: "نام بازی": jdatetime.datetime(سال, ماه, روز, ساعت, دقیقه)
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

# --- توابع کمکی ---
def normalize_str(text):
    text = text.replace('ي', 'ی').replace('ك', 'ک')
    text = text.replace("‌", "")  # حذف نیم‌فاصله
    return "".join(text.split()).lower()

def extract_teams(match_text):
    """
    جداکننده‌های مختلف مثل:
    vs, VS, vS, Vs, -, –, —
    را پشتیبانی می‌کند.
    """
    pattern = r'\s*(?:vs|v\.s|v\s*s|-|–|—)\s*'
    parts = re.split(pattern, match_text, flags=re.IGNORECASE)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) != 2:
        return None

    return normalize_str(parts[0]), normalize_str(parts[1])

def match_any_order(user_text, match_key):
    user_norm = normalize_str(user_text)
    teams = extract_teams(match_key)
    if not teams:
        return False

    team1, team2 = teams
    return team1 in user_norm and team2 in user_norm

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

    # 1) پردازش /show
    if msg_text == "/show":
        data = load_data()
        summary = f"📋 {TITLE}\n\n"
        for match in MATCHES:
            ball = GAME_BALLS.get(match, "⚪")
            prediction = data.get(match, "ثبت نشده")
            summary += f"{ball} {match}\n   └ 🔮 {prediction}\n\n"
        send_message(chat_id, summary)
        return

    # 2) تشخیص اینکه کاربر اسم مسابقه را نوشته یا نه
    lines = msg_text.split('\n')
    match_input = lines[0].strip()

    matched_match = None
    for m in MATCHES:
        if match_any_order(match_input, m):
            matched_match = m
            break

    # اگر بازی پیدا نشد، چیزی نگو
    if not matched_match:
        return

    # 3) بررسی زمان و ثبت پیش‌بینی
    if jdatetime.datetime.now() > MATCHES[matched_match]:
        send_message(chat_id, f"❌ متأسفم، زمان پیش‌بینی برای بازی {matched_match} تمام شده است.")
        return

    if len(lines) >= 2:
        prediction_input = lines[1].strip()
        if not prediction_input:
            send_message(chat_id, "لطفاً در خط دوم پیش‌بینی خود را بنویسید.")
            return

        data = load_data()
        data[matched_match] = prediction_input
        save_data(data)
        send_message(chat_id, f"{GAME_BALLS.get(matched_match, '✅')} پیش‌بینی شما ثبت شد.")
    else:
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

