import os
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set!")
    
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app = Flask(__name__)

BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
users_db = {}

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/pocket_postback')
def pocket_postback():
    subid = request.args.get('subid')
    sum_val = request.args.get('sum', '0')
    try:
        amount = float(sum_val)
        tg_id = int(subid)
    except:
        return "invalid", 400
    user = users_db.get(tg_id, {"total":0})
    total = user.get("total",0) + amount
    user["total"] = total
    if total >= 100: level="vip"
    elif total >= 50: level="pro"
    else: level="starter"
    user["level"]=level
    user["verified"]=True
    users_db[tg_id]=user
    if bot:
        try:
            bot.send_message(tg_id, f"✅ Deposit ${amount} confirmed! Total ${total} Level {level.upper()}")
        except: pass
    return "ok",200

@bot.message_handler(commands=['start'])
def start(m):
    link = f"{BASE_AFF_LINK}?click_id={m.from_user.id}"
    bot.send_message(m.chat.id, f"Register here: {link}\nThen deposit $20+. I will auto-detect!")

if __name__ == "__main__":
    import threading
    def run_bot():
        if bot: bot.infinity_polling()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
