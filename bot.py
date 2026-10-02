import os
import json
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
DB_FILE = "users.json"
OWNER_ID = "8188622130"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

users_db = load_db()

SIGNALS = {
    "starter": "📊 STARTER Signal:\nAsset: EUR/USD\nAction: BUY ⬆️\nTime: 2 min\nConfidence: 75%",
    "pro": "📊 PRO Signal:\nAsset: GBP/USD\nAction: SELL ⬇️\nTime: 3 min\nConfidence: 85%",
    "vip": "🔥 VIP Signal:\nAsset: BTC/USD\nAction: BUY ⬆️\nTime: 5 min\nConfidence: 92%\nAnalysis: Breakout confirmed"
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
        tg_id = str(int(float(subid)))
    except:
        return "invalid", 400
    user = users_db.get(tg_id, {"total": 0, "level": "none"})
    total = user.get("total", 0) + amount
    if total >= 100:
        level = "vip"
    elif total >= 50:
        level = "pro"
    else:
        level = "starter"
    user["total"] = total
    user["level"] = level
    user["verified"] = True
    users_db[tg_id] = user
    save_db(users_db)
    try:
        bot.send_message(int(tg_id), f"✅ Deposit ${amount} confirmed!\nTotal: ${total}\nLevel: {level.upper()} 🎉\nNow send /signals")
    except:
        pass
    return "ok", 200

@bot.message_handler(commands=['start'])
def start(m):
    tid = str(m.from_user.id)
    if tid not in users_db:
        users_db[tid] = {"total": 0, "level": "none", "verified": False}
        save_db(users_db)
    link = f"{BASE_AFF_LINK}?click_id={m.from_user.id}"
    if tid == OWNER_ID:
        bot.send_message(m.chat.id, f"👑 WELCOME OWNER!\nID: {m.from_user.id}\nFull VIP access\nLink: {link}\n/signals /balance /users")
    else:
        bot.send_message(m.chat.id, f"👋 Welcome!\nRegister: {link}\nDeposit $20+\nYour ID: {m.from_user.id}\n/signals /balance")

@bot.message_handler(commands=['balance'])
def balance(m):
    tid = str(m.from_user.id)
    user = users_db.get(tid, {"total": 0, "level": "none"})
    owner_tag = " (OWNER 👑)" if tid == OWNER_ID else ""
    bot.send_message(m.chat.id, f"💰 Balance: ${user.get('total', 0)}\n🏆 Level: {user.get('level', 'none').upper()}{owner_tag}\n✅ Verified: {user.get('verified', False) or tid == OWNER_ID}")

@bot.message_handler(commands=['signals'])
def signals(m):
    tid = str(m.from_user.id)
    if tid == OWNER_ID:
        bot.send_message(m.chat.id, f"👑 OWNER VIP ACCESS\n\n{SIGNALS['vip']}\n\n🔥 Unlimited!")
        return
    user = users_db.get(tid)
    if not user or not user.get("verified"):
        bot.send_message(m.chat.id, "❌ Not verified! Deposit $20 first.\nUse /start to get link")
        return
    level = user.get("level", "starter")
    bot.send_message(m.chat.id, SIGNALS.get(level, SIGNALS["starter"]))

@bot.message_handler(commands=['users'])
def users_list(m):
    tid = str(m.from_user.id)
    if tid!= OWNER_ID:
        bot.send_message(m.chat.id, "❌ Owner only!")
        return
    total_users = len(users_db)
    total_deposits = sum([u.get("total", 0) for u in users_db.values()])
    msg = f"👑 OWNER STATS\nUsers: {total_users}\nDeposits: ${total_deposits}\n\n"
    for uid, data in list(users_db.items())[:10]:
        msg += f"{uid}: ${data.get('total', 0)} - {data.get('level', 'none')}\n"
    bot.send_message(m.chat.id, msg)

if __name__ == "__main__":
    import threading
    def run_bot():
        bot.infinity_polling()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
