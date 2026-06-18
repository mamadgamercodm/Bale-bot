
import requests
import json
import os
import jdatetime
import time

# =========================
# تنظیمات اصلی (خواندن توکن از متغیر محیطی)
# =========================
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("توکن ربات در متغیرهای محیطی یافت نشد!")

API_URL = f"https://tapi.bale.ai/bot{TOKEN}/"
DATA_FILE = "data.json"
TITLE = "WORLDCUP PREDICTION 69"

# =========================
# لیست بازی‌ها و توپ‌های رنگی
# =========================
MATCHES = {
    "آفریقا جنوبی vs جمهوری چک": jdatetime.datetime(1405, 3, 28, 19, 30, 0),
    "بوسنی vs سوییس": jdatetime.datetime(1405, 3, 28, 22, 30, 0),
    "کانادا vs قطر": jdatetime.datetime(1405, 3, 29, 1, 30, 0),
    "مکزیک vs کره جنوبی": jdatetime.datetime(1405, 3, 29, 4, 30, 0)
}

GAME_BALLS = {
    "آفریقا جنوبی vs جمهوری چک": "🔵",
    "بوسنی vs سوییس": "🟢",
    "کانادا vs قطر": "🔴",
    "مکزیک vs کره جنوبی": "🟡"
}

# =========================
# توابع کمکی
# =========================
def normalize_str(text):
    if not isinstance(text, str):
        return ""
    return text.replace('ك', 'ک').replace('ي', 'ی').replace('ى', 'ی').strip()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {TITLE: {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {TITLE: {}}
    except:
        return {TITLE: {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_message(chat_id, text):
    try:
        payload = {"chat_id": chat_id, "text": text}
        requests.post(API_URL + "sendMessage", json=payload, timeout=20)
    except Exception as e:
        print(f"خطای ارسال: {e}")

def format_predictions_summary(data):
    predictions_data = data.get(TITLE, {})
    if not isinstance(predictions_data, dict):
        predictions_data = {}

    summary = f"🟣🟣 {TITLE} 🟣🟣\n\n"
    for game_name in MATCHES.keys():
        ball = GAME_BALLS.get(game_name, "🟣")
        summary += f"⚽ بازی: {game_name}\n"
        game_predictions = predictions_data.get(game_name, [])
        if not game_predictions:
            summary += f"   {ball} (هنوز پیش‌بینی ثبت نشده)\n"
        else:
            for p in game_predictions:
                if isinstance(p, dict):
                    summary += f"   {ball} {p.get('result', '-')}\n"
        summary += f"   {ball} ────────────────────\n"
    return summary.strip()

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.strip() == "/show":
        data = load_data()
        send_message(chat_id, format_predictions_summary(data))
        return

    lines = text.strip().split('\n')
    if len(lines) < 2:
        return

    game_input = normalize_str(lines[0])
    prediction = lines[1].strip()

    found_game = next((g for g in MATCHES.keys() if normalize_str(g) == game_input), None)
    if not found_game:
        return

    data = load_data()
    if TITLE not in data: data[TITLE] = {}
    if found_game not in data[TITLE]: data[TITLE][found_game] = []
    
    data[TITLE][found_game].append({"result": prediction})
    save_data(data)
    send_message(chat_id, format_predictions_summary(data))

def main():
    last_update_id = 0
    print("ربات فعال شد...")
    while True:
        try:
            response = requests.get(
                API_URL + "getUpdates",
                params={"offset": last_update_id + 1, "timeout": 30},
                timeout=40
            )
            updates = response.json().get("result", [])
            for update in updates:
                last_update_id = update["update_id"]
                if "message" in update and "text" in update["message"]:
                    handle_message(update["message"])
        except Exception as e:
            print(f"خطا در دریافت آپدیت‌ها: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
