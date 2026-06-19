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

# --- لیست مسابقات به همراه زمان قفل ---
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
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_message(chat_id, text):
    url = API_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

def format_summary(data):
    summary = f"📋 {TITLE}\n\n"
    for match in MATCHES:
        ball = GAME_BALLS.get(match, "⚪")
        preds = data.get(match, [])
        summary += f"{ball} {match}\n"
        if not preds:
            summary += "   └ 🔮 هنوز پیش‌بینی‌ای ثبت نشده\n\n"
        else:
            for p in preds:
                user_label = p.get("username") or p.get("first_name") or f"User {p.get('user_id', '')}"
                prediction = p.get("prediction", "")
                summary += f"   └ 👤 {user_label}: {prediction}\n"
            summary += "\n"
    return summary.strip()

def process_update(update):
    if 'message' not in update or 'text' not in update['message']:
        return

    msg = update['message']
    msg_text = msg['text'].strip()
    chat_id = msg['chat']['id']

    user = msg.get('from', {})
    user_id = user.get('id')
    username = user.get('username', '')
    first_name = user.get('first_name', 'کاربر')

    # /show
    if msg_text == "/show":
        data = load_data()
        send_message(chat_id, format_summary(data))
        return

    # خطوط ورودی
    lines = [line.strip() for line in msg_text.split('\n') if line.strip()]
    if len(lines) < 2:
        send_message(chat_id, "لطفاً در خط اول نام بازی و در خط‌های بعدی پیش‌بینی‌ها را بنویسید.")
        return

    match_input = lines[0]

    matched_match = None
    for m in MATCHES:
        if match_any_order(match_input, m):
            matched_match = m
            break

    if not matched_match:
        return

    # بررسی زمان
    if jdatetime.datetime.now() > MATCHES[matched_match]:
        send_message(chat_id, f"❌ متأسفم، زمان پیش‌بینی برای بازی {matched_match} تمام شده است.")
        return

    predictions = lines[1:]
    if not predictions:
        send_message(chat_id, "لطفاً در خط دوم پیش‌بینی خود را بنویسید.")
        return

    data = load_data()
    if matched_match not in data:
        data[matched_match] = []

    for pred in predictions:
        data[matched_match].append({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "prediction": pred
        })

    save_data(data)

    send_message(chat_id, f"✅ {len(predictions)} پیش‌بینی برای {matched_match} ثبت شد.\n\n{format_summary(data)}")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update:
        process_update(update)
    return 'ok', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
