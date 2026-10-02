import os
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Put your bot token in Railway Variables
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Your affiliate link - WW
BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"

# Simple memory DB - replace with real DB later
users_db = {}

def get_level(total):
    if total >= 100:
        return "vip"
    elif total >= 50:
        return "pro"
    else:
        return "starter"

@app.route('/')
def home():
    return "Bot is running!"

# --- THIS IS THE AUTOMATIC POSTBACK ---
@app.route('/pocket_postback')
def pocket_postback():
    subid = request.args.get('subid')  # Telegram ID from CLICK_ID
    sum_str = request.args.get('sum', '0')
    try:
        amount = float(sum_str)
        tg_id = int(subid)
    except:
        return "invalid params", 400
    
    user = users_db.get(tg_id)
    if not user:
        # User not in bot yet, but we still store
        users_db[tg_id] = {"total": 0}
        user = users_db[tg_id]
    
    total = user.get("total", 0) + amount
    user["total"] = total
    user["level"] = get_level(total)
    user["verified"] = True
    
    # Notify user in Telegram automatically
    try:
        level = user["level"].upper()
        bot.send_message(tg_id, 
            f"✅ *Deposit Confirmed!* ${amount}\n\n"
            f"💰 Total Deposited: ${total}\n"
            f"⭐ Your Level: {level}\n\n"
            f"Level system:\n"
            f"• Starter: $20+\n"
            f"• Pro: $50+\n"
            f"• VIP: $100+\n\n"
            f"Send /signals to get signals!",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending msg: {e}")
    
    return "ok", 200

# --- TELEGRAM BOT ---
@bot.message_handler(commands=['start'])
def start(message):
    tg_id = message.from_user.id
    if tg_id not in users_db:
        users_db[tg_id] = {"total": 0, "level": "none", "verified": False}
    
    # Create link WITH telegram ID
    aff_link = f"{BASE_AFF_LINK}?click_id={tg_id}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 Create Pocket Account", url=aff_link))
    markup.add(types.InlineKeyboardButton("✅ I Deposited - Check", callback_data="check"))
    
    bot.send_message(message.chat.id,
        f"👋 Welcome! To activate bot:\n\n"
        f"1. Click button below to register Pocket account\n"
        f"2. Deposit minimum $20\n"
        f"3. Bot will AUTO-DETECT deposit and upgrade you!\n\n"
        f"Your ID: {tg_id}",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check(call):
    tg_id = call.from_user.id
    user = users_db.get(tg_id, {"total": 0, "level": "none"})
    total = user.get("total", 0)
    level = user.get("level", "none")
    
    if user.get("verified"):
        bot.answer_callback_query(call.id, "Verified!")
        bot.send_message(tg_id, f"✅ You are verified! Total: ${total} | Level: {level.upper()}")
    else:
        bot.answer_callback_query(call.id, "Not yet deposited")
        bot.send_message(tg_id, f"⏳ Not yet detected. Total so far: ${total}\n\nMake sure you registered with link that has your ID: {tg_id}\nLink: {BASE_AFF_LINK}?click_id={tg_id}")

if __name__ == "__main__":
    # Run both bot and flask
    import threading
    def run_bot():
        bot.infinity_polling()
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
