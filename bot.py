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
    "راکش vs اسکاتلند": "🟢",
    "هاييتي vs برزيل": "",
    "پاراگوئه vs ترکيه": "🟡"
}

# --- توابع کمکی
