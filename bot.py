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

# --- توابع کمکی ---
def normalize_str(text):
    text = text.replace('ي', 'ی').replace('ك', 'ک')
    text = text.replace("‌", "")
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
    if not teams: return False
    team1, team2 = teams
    return team1 in user_norm and team2 in user_norm

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_message(chat_id, text):
    try:
        requests.post(API_URL + "sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Error sending message: {e}")

def format_summary(chat_id, data):
    """نمایش خلاصه فقط برای یک گروه خاص"""
    summary = f"📋 {TITLE}\n\n"
    # دریافت داده‌های مربوط به این چت خاص
    chat_data = data.get(str(chat_id), {})
    
    for match in MATCHES:
        ball = GAME_BALLS.get(match, "⚪")
        preds = chat_data.get(match, [])
        summary += f"{ball} {match}\n"
        if not preds:
            summary += "   └ 🔮 هنوز پیش‌بینی‌ای ثبت نشده\n\n"
        else:
            for p in preds:
                user_label = p.get("username") or p.get("first_name") or f"User {p.get('user_id', '')}"
                summary += f"   └ 👤 {user_label}: {p.get('prediction')}\n"
            summary += "\n"
    return summary.strip()

def process_update(update):
    if 'message' not in update or 'text' not in update['message']:
        return

    msg = update['message']
    msg_text = msg['text'].strip()
    chat_id = msg['chat']['id']

    # اصلاح هوشمند دستورات: بررسی اینکه آیا با /show یا /pred شروع می‌شود (حتی با @b
    is_show = msg_text.startswith("/show")
    is_pred = msg_text.startswith("/pred")
    
    if not is_show and not is_pred:
        return 

    # پردازش /show
    if is_show:
        all_data = load_data()
        send_message(chat_id, format_summary(chat_id, all_data))
        return

    # پردازش /pred
    # حذف عبارت /pred و هر چیزی که بعد از آن با @ شروع می‌شود (مثل /pred@mybot)
    content = re.sub(r'^/pred(@\S+)?', '', msg_text).strip()
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    if len(lines) < 2:
        send_message(chat_id, "⚠️ فرمت صحیح:\n/pred\nنام بازی\nپیش‌بینی")
        return

    match_input = lines[0]
    matched_match = next((m for m in MATCHES if match_any_order(match_input, m)), None)

    if not matched_match:
        send_message(chat_id, "❌ بازی مورد نظر پیدا نشد. لطفاً نام تیم‌ها را درست وارد کنید.")
        return

    if jdatetime.datetime.now() > MATCHES[matched_match]:
        send_message(chat_id, f"❌ زمان پیش‌بینی برای {matched_match} تمام شده.")
        return

    # ذخیره با تفکیک chat_id برای جلوگیری از تداخل گروه‌ها
    user = msg.get('from', {})
    all_data = load_data()
    
    chat_id_str = str(chat_id)
    if chat_id_str not in all_data:
        all_data[chat_id_str] = {}
    
    if matched_match not in all_data[chat_id_str]:
        all_data[chat_id_str][matched_match] = []
    
    for pred in lines[1:]:
        all_data[chat_id_str][matched_match].append({
            "user_id": user.get('id'),
            "username": user.get('username', ''),
            "first_name": user.get('first_name', 'کاربر'),
            "prediction": pred
        })
    
    save_data(all_data)
    send_message(chat_id, f"✅ ثبت شد:\n\n{format_summary(chat_id, all_data)}")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update: 
        process_update(update)
    return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
