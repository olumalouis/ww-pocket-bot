import telebot
from telebot import types
import random
import threading
import time
import os
from datetime import datetime, timezone
from flask import Flask, request

BOT_TOKEN=os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID=8188622130
AFFILIATE_LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"

pairs_real=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","GBP/JPY","AUD/JPY","EUR/AUD","USD/CHF","NZD/USD","EUR/CAD","GBP/CAD","AUD/CAD"]
pairs_otc=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/JPY OTC","EUR/GBP OTC","GBP/JPY OTC","AUD/JPY OTC","EUR/AUD OTC","USD/CHF OTC","NZD/USD OTC","EUR/CAD OTC","GBP/CAD OTC","AUD/CAD OTC","EUR/NZD OTC","GBP/NZD OTC","GBP/AUD OTC","AUD/NZD OTC","EUR/CHF OTC","GBP/CHF OTC","CHF/JPY OTC","AUD/CHF OTC","CAD/CHF OTC","USD/BRL OTC","EUR/BRL OTC","USD/INR OTC","USD/TRY OTC","EUR/TRY OTC","USD/ZAR OTC"]

bot=telebot.TeleBot(BOT_TOKEN)
app=Flask(__name__)
users={}

@app.route('/')
def home():
    return "BOT ALIVE"

def ensure_user(uid, name):
    if uid not in users:
        users[uid]={"deposit":0,"registered":False}
    return users[uid]

def get_level(uid):
    if uid==OWNER_ID:
        return "VIP"
    if uid not in users or not users[uid].get("registered"):
        return "LOCKED"
    dep=users[uid].get("deposit",0)
    if dep>=100: return "VIP"
    if dep>=50: return "PRO"
    if dep>=20: return "STARTER"
    return "NONE"

@app.route('/postback')
def postback():
    click_id=request.args.get('click_id')
    deposit=request.args.get('deposit','0')
    try:
        uid=int(click_id)
        dep=int(float(deposit))
        ensure_user(uid,f"User{uid}")
        users[uid]["registered"]=True
        users[uid]["deposit"]=max(users[uid].get("deposit",0),dep)
        return f"OK {uid}",200
    except:
        return "ERROR",400

def main_menu():
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("GET SIGNAL","REAL 15")
    markup.add("OTC 30","My Status")
    markup.add("Admin Panel")
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid=m.from_user.id
    ensure_user(uid,m.from_user.first_name)
    lvl=get_level(uid)
    if lvl=="LOCKED" and uid!=OWNER_ID:
        bot.send_message(m.chat.id,f"LOCKED. Register: {AFFILIATE_LINK}?subid={uid}")
    else:
        bot.send_message(m.chat.id,f"Welcome {lvl}",reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    bot.send_message(m.chat.id,"Bot working! Use /start",reply_markup=main_menu())

def run_bot():
    print("FIXED 409 - DELETING WEBHOOK")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted")
    except Exception as e:
        print(e)
    while True:
        try:
            print("🚀 Polling...")
            bot.infinity_polling(skip_pending=True,timeout=20,long_polling_timeout=20)
        except Exception as e:
            print(f"Crash {e} retry 5s")
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)
