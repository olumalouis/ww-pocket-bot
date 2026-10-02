import os
import json
import random
from datetime import datetime, date
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set!")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
DB_FILE = "users.json"
OWNER_ID = "8188622130"

ALL_PAIRS_REAL = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/GBP", "NZD/USD", "EUR/AUD", "GBP/JPY", "BTC/USD", "ETH/USD"]
ALL_PAIRS_OTC = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "EUR/JPY OTC", "GBP/JPY OTC", "BTC/USD OTC", "ETH/USD OTC", "EUR/GBP OTC", "USD/BRL OTC"]

TIERS = {
    "starter": {"pairs": ["EUR/USD", "USD/JPY", "GBP/USD", "EUR/USD OTC", "USD/JPY OTC", "GBP/USD OTC"], "expiry_real": ["1m"], "expiry_otc": ["15s", "30s", "1m"], "name": "STARTER"},
    "pro": {"pairs": ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC"], "expiry_real": ["1m", "2m", "3m"], "expiry_otc": ["15s", "30s", "1m", "2m", "3m"], "name": "PRO"},
    "vip": {"pairs": ALL_PAIRS_REAL + ALL_PAIRS_OTC, "expiry_real": ["1m", "2m", "3m", "5m"], "expiry_otc": ["15s", "30s", "1m", "2m", "3m", "5m"], "name": "VIP"}
}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

users_db = load_db()

def get_user_level(tid):
    if str(tid) == OWNER_ID: return "vip"
    u = users_db.get(str(tid))
    if not u or not u.get("verified"): return None
    return u.get("level", "starter")

def generate_signal_text(pair, expiry, level):
    action = random.choice(["BUY ⬆️", "SELL ⬇️"])
    conf = {"starter": random.randint(72,80), "pro": random.randint(81,88), "vip": random.randint(89,95)}[level]
    market_type = "OTC" if "OTC" in pair else "REAL"
    return f"🎯 *{level.upper()} SIGNAL*\n\n💱 Pair: {pair}\n📊 Market: {market_type}\n⏰ Expiry: {expiry}\n📈 Action: {action}\n🔥 Confidence: {conf}%\n\nUTC: {datetime.utcnow().strftime('%H:%M')} UTC"

@app.route('/')
def home(): return "V2 Bot Active - Deposit Only!"

@app.route('/pocket_postback')
def pocket_postback():
    subid = request.args.get('subid')
    sum_val = request.args.get('sum', '0')
    try:
        amount = float(sum_val)
        tg_id = str(int(float(subid)))
    except: return "invalid", 400
    user = users_db.get(tg_id, {"total":0, "level":"none", "referrals":0, "invited_by":None})
    total = user.get("total",0) + amount
    if total >= 100: level = "vip"
    elif total >= 50: level = "pro"
    else: level = "starter"
    user["total"] = total
    user["level"] = level
    user["verified"] = True
    users_db[tg_id] = user
    save_db(users_db)
    try:
        bot.send_message(int(tg_id), f"✅ Deposit ${amount} confirmed!\nTotal: ${total}\nLevel: {level.upper()} 🎉")
    except: pass
    return "ok", 200

@bot.message_handler(commands=['start'])
def start(m):
    tid = str(m.from_user.id)
    args = m.text.split()
    invited_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try: invited_by = args[1].replace("ref_","")
        except: pass
    if tid not in users_db:
        users_db[tid] = {"total":0, "level":"none", "verified":False, "referrals":0, "invited_by":invited_by, "last_teaser":None}
        if invited_by and invited_by in users_db and invited_by!= tid:
            ref_user = users_db[invited_by]
            ref_user["referrals"] = ref_user.get("referrals",0)+1
            if ref_user["referrals"] % 3 == 0:
                try: bot.send_message(int(invited_by), f"🎉 Referral Bonus! You invited 3 friends = +1 Day VIP FREE!")
                except: pass
        save_db(users_db)
    link = f"{BASE_AFF_LINK}?click_id={tid}"
    try:
        username = bot.get_me().username
    except:
        username = "WWPocketSignalsbot"
    ref_link = f"https://t.me/{username}?start=ref_{tid}"
    kb = types.Inline
