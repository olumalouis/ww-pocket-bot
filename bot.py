import os, threading, telebot
from flask import Flask
app = Flask(__name__)
@app.route('/')
def h(): return 'ok'

TOKEN = os.getenv("BOT_TOKEN").strip()
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)
print("TEST BOT STARTING")

@bot.message_handler(commands=['start'])
def start(m):
    print(f"RECEIVED /start FROM {m.from_user.id}")
    bot.send_message(m.chat.id, f"✅ ALIVE! Your ID: {m.from_user.id}\nSend /start again and I reply.")

@bot.message_handler(func=lambda x: True)
def any_msg(m):
    print(f"MSG from {m.from_user.id}: {m.text}")
    bot.send_message(m.chat.id, f"Got: {m.text}")

def run():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
