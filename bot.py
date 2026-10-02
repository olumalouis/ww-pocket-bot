import os, json
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
DB_FILE = "users.json"
OWNER_ID = "8188622130" # YOUR OWNER ID - FULL ACCESS

# Load DB
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

users_db = load_db()

# Signals for each level
SIGNALS = {
    "starter": "📊 STARTER Signal:\nAsset: EUR/USD\nAction: BUY ⬆️\nTime: 2 min\nConfidence: 75%",
    "pro": "📊 PRO Signal:\nAsset: GBP/USD\nAction: SELL ⬇️\nTime: 3 min\nConfidence: 85%\nReason: Strong downtrend + RSI overbought",
    "vip": "🔥 VIP Signal:\nAsset: BTC/USD\nAction: BUY ⬆️\nTime: 5 min\nConfidence: 92%\nAnalysis: Breakout + Volume spike + 3 indicators align\nEntry: Now"
}

@app.route('/')
def home():
    return "Bot Active!"

@app.route('/pocket_postback')
def pocket_postback():
    subid = request.args.get('subid')
    sum_val = request.args.get('sum', '0')
    try:
        amount = float(sum_val)
        tg_id = str(int(subid))
    except:
        return "invalid", 400

    user = users_db.get(tg_id, {"total":0, "level":"none"})
    total = user.get("total",0) + amount
    if total >= 100: level="vip"
    elif total >= 50: level="pro"
    else: level="starter"

    user["total"] = total
    user["level"] = level
    user["verified"] = True
    users_db[tg_id] = user
    save_db(users_db)

    try:
        bot.send_message(int(tg_id), f"✅ Deposit ${amount} confirmed!\nTotal: ${total}\nLevel: {level.upper()} 🎉\n\nNow send /signals to get signals!")
    except: pass
    return "ok",200

@bot.message_handler(commands=['start'])
def start(m):
    tid = str(m.from_user.id)
    if tid not in users_db:
        users_db[tid] = {"total":0, "level":"none", "verified":False}
        save_db(users_db)
    link = f"{BASE_AFF_LINK}?click_id={m.from_user.id}"
    # Owner message
    if tid == OWNER_ID:
        bot.send_message(m.chat.id, f"👑 WELCOME OWNER!\nYour ID: {m.from_user.id}\n\nYou have FULL VIP ACCESS\n\nYour affiliate link:\n{link}\n\nCommands:\n/signals - Get VIP signals\n/balance - Check stats\n/users - See all users (owner only)")
    else:
        bot.send_message(m.chat.id, f"👋 Welcome!\n\n1️⃣ Register: {link}\n2️⃣ Deposit $20+\n3️⃣ I auto-detect deposit\n\nYour ID: {m.from_user.id}\n\nCommands:\n/signals - Get signals\n/balance - Check level")

@bot.message_handler(commands=['balance'])
def balance(m):
    tid = str(m.from_user.id)
    user = users_db.get(tid, {"total":0, "level":"none"})
    is_owner = " (OWNER 👑)" if tid == OWNER_ID else ""
    bot.send_message(m.chat.id, f"💰 Balance: ${user.get('total',0)}\n🏆 Level: {user.get('level','none').upper()}{is_owner}\n✅ Verified: {user.get('verified',False) or tid==OWNER_ID}")

@bot.message_handler(commands=['signals
