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
AFFILIATE_LINK="https://pocket-option.com/en/cabinet/try-demo/?lid=1154235"

pairs_real=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","GBP/JPY","AUD/JPY","EUR/AUD","USD/CHF","NZD/USD","EUR/CAD","GBP/CAD","AUD/CAD"]
pairs_otc=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/JPY OTC","EUR/GBP OTC","GBP/JPY OTC","AUD/JPY OTC","EUR/AUD OTC","USD/CHF OTC","NZD/USD OTC","EUR/CAD OTC","GBP/CAD OTC","AUD/CAD OTC","EUR/NZD OTC","GBP/NZD OTC","GBP/AUD OTC","AUD/NZD OTC","EUR/CHF OTC","GBP/CHF OTC","CHF/JPY OTC","AUD/CHF OTC","CAD/CHF OTC","USD/BRL OTC","EUR/BRL OTC","USD/INR OTC","USD/TRY OTC","EUR/TRY OTC","USD/ZAR OTC"]
MOTIV_WORDS=["STAY STRONG","NEXT IS WIN","DON'T GIVE UP","FOCUS","YOU GOT THIS","KEEP GOING","STAY CALM","BIG WIN COMING","BELIEVE","PUSH HARD"]

bot=telebot.TeleBot(BOT_TOKEN)
app=Flask(__name__)
users={}
last_bot_msgs={}
broadcast_wait={}

@app.route('/')
def home():
    return "✅ WW POCKET SIGNALS V13.2.9 Alive"

def ensure_user(uid, name):
    if uid not in users:
        users[uid]={"id":uid,"name":name,"deposit":0,"wins":0,"losses":0,"gwr_wins":0,"gwr_losses":0,"streak":0,"loss_streak":0,"limit":0,"used":0,"last_reset":datetime.now(timezone.utc).date().isoformat(),"banned":False,"bcast_wait":None,"registered":False}
    return users[uid]

def get_level(uid):
    if uid==OWNER_ID:
        return "VIP"
    if uid not in users:
        return "LOCKED"
    if not users[uid].get("registered", False):
        return "LOCKED"
    dep=users[uid].get("deposit",0)
    if dep>=100:
        return "VIP"
    if dep>=50:
        return "PRO"
    if dep>=20:
        return "STARTER"
    return "NONE"

def get_limit(level):
    if level=="LOCKED":
        return 0
    if level=="VIP":
        return 1000000
    if level=="PRO":
        return 100
    if level=="STARTER":
        return 20
    if level=="NONE":
        return 5
    return 0

def check_daily(uid):
    today=datetime.now(timezone.utc).date().isoformat()
    if users[uid].get("last_reset")!=today:
        users[uid]["wins"]=0
        users[uid]["losses"]=0
        users[uid]["streak"]=0
        users[uid]["loss_streak"]=0
        users[uid]["used"]=0
        users[uid]["last_reset"]=today
        users[uid]["limit"]=get_limit(get_level(uid))

@app.route('/postback')
def postback():
    click_id=request.args.get('click_id')
    deposit=request.args.get('deposit', '0')
    try:
        uid=int(click_id)
        dep=int(float(deposit))
        if uid not in users:
            users[uid]={"id":uid,"name":f"User{uid}","deposit":0,"wins":0,"losses":0,"gwr_wins":0,"gwr_losses":0,"streak":0,"loss_streak":0,"limit":0,"used":0,"last_reset":datetime.now(timezone.utc).date().isoformat(),"banned":False,"bcast_wait":None,"registered":True}
        users[uid]["registered"]=True
        users[uid]["deposit"]=max(users[uid].get("deposit",0), dep)
        users[uid]["limit"]=get_limit(get_level(uid))
        return f"OK {uid}", 200
    except:
        return "ERROR", 400

def main_menu():
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📊 GET SIGNAL"), types.KeyboardButton("✅ REAL 15"))
    markup.add(types.KeyboardButton("🔶 OTC 30"), types.KeyboardButton("💎 Upgrade"))
    markup.add(types.KeyboardButton("💰 Deposit"), types.KeyboardButton("📈 My Status"))
    markup.add(types.KeyboardButton("📜 How it Works"), types.KeyboardButton("👑 Admin Panel"))
    return markup

def locked_message(uid):
    link=f"{AFFILIATE_LINK}?subid={uid}"
    markup=types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 Register Now - Unlock 5/day FREE", url=link))
    markup.add(types.InlineKeyboardButton("📜 How it Works", callback_data="howitworks"))
    text=f"🔒 WELCOME TO WW POCKET SIGNALS BOT\n\n🔒 YOU ARE LOCKED\n1️⃣ Register via link with?subid={uid}\n2️⃣ Get 5/day FREE\n⚪ NONE 5/day\n🟢 STARTER $20 20/day\n🔵 PRO $50 100/day\n💎 VIP $100 UNLIMITED"
    return text, markup

def track_msg(chat_id, msg):
    if chat_id not in last_bot_msgs:
        last_bot_msgs[chat_id]=[]
    last_bot_msgs[chat_id].append(msg.message_id)
    if len(last_bot_msgs[chat_id])>15:
        last_bot_msgs[chat_id]=last_bot_msgs[chat_id][-15:]

def clean_and_track(chat_id, uid):
    if chat_id in last_bot_msgs:
        for mid in last_bot_msgs[chat_id]:
            try:
                bot.delete_message(chat_id, mid)
            except:
                pass
        last_bot_msgs[chat_id]=[]

def get_signal_with_indicators():
    rsi=round(random.uniform(18,82),1)
    price=round(random.uniform(1.0500,1.3500),4)
    ema200=round(price + random.uniform(-0.0150,0.0150),4)
    above=price>ema200
    if rsi<30:
        rsi_label=f"RSI {rsi} Oversold"
        rsi_type="bullish"
    elif rsi<45:
        rsi_label=f"RSI {rsi} Bullish"
        rsi_type="bullish"
    elif rsi<=55:
        rsi_label=f"RSI {rsi} Neutral"
        rsi_type="neutral"
    elif rsi<=70:
        rsi_label=f"RSI {rsi} Bearish"
        rsi_type="bearish"
    else:
        rsi_label=f"RSI {rsi} Overbought"
        rsi_type="bearish"
    ema_label=f"EMA200 Price {price} {'Above' if above else 'Below'}"
    ema_type="bullish" if above else "bearish"
    if rsi_type=="bullish" and ema_type=="bullish":
        direction="BUY 📈"
        strength="Strong Bullish"
    elif rsi_type=="bearish" and ema_type=="bearish":
        direction="SELL 📉"
        strength="Strong Bearish"
    elif rsi_type=="bullish":
        direction="BUY 📈"
        strength="Bullish"
    else:
        direction="SELL 📉"
        strength="Bearish"
    return direction, strength, rsi_label, ema_label@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_buttons(m):
    uid=m.from_user.id
    txt=(m.text or "")
    txt_up=txt.upper()
    if uid not in users:
        ensure_user(uid, m.from_user.username or m.from_user.first_name)
    if users[uid].get("banned"):
        bot.send_message(m.chat.id, "⛔ You are banned")
        return
    check_daily(uid)
    lvl=get_level(uid)
    if lvl=="LOCKED" and "HOW IT WORKS" not in txt_up and "ADMIN PANEL" not in txt_up and "/START" not in txt_up:
        if any(k in txt_up for k in ["GET SIGNAL","REAL 15","OTC 30","MY STATUS","UPGRADE","DEPOSIT"]):
            text, markup=locked_message(uid)
            msg=bot.send_message(m.chat.id, text, reply_markup=markup)
            track_msg(m.chat.id, msg)
            return
    if "GET SIGNAL" in txt_up:
        if lvl=="LOCKED":
            text, markup=locked_message(uid)
            msg=bot.send_message(m.chat.id, text, reply_markup=markup)
            track_msg(m.chat.id, msg)
            return
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✅ REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        msg=bot.send_message(m.chat.id, "🔥 Select Market:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "REAL 15" in txt_up:
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 15", callback_data="manual_real"), types.InlineKeyboardButton("🤖 Auto", callback_data="auto_real"))
        msg=bot.send_message(m.chat.id, "💹 REAL 15 Market:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "OTC 30" in txt_up:
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 30", callback_data="manual_otc"), types.InlineKeyboardButton("🤖 Auto 30", callback_data="auto_otc"))
        msg=bot.send_message(m.chat.id, "🔶 OTC 30 Market:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "MY STATUS" in txt_up:
        wins=users[uid].get('wins',0)
        losses=users[uid].get('losses',0)
        msg=bot.send_message(m.chat.id, f"📈 MY STATUS\nWins: {wins}\nLosses: {losses}", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "UPGRADE" in txt_up:
        link=f"{AFFILIATE_LINK}?subid={uid}"
        level=get_level(uid)
        markup=types.InlineKeyboardMarkup()
        if level=="VIP":
            markup.add(types.InlineKeyboardButton("💎 You are VIP 👑", url=link))
            upgrade_text=f"🎉 YOU ARE VIP - UNLIMITED!"
        else:
            markup.add(types.InlineKeyboardButton("🟢 STARTER $20 20/day", url=link))
            markup.add(types.InlineKeyboardButton("🔵 PRO $50 100/day", url=link))
            markup.add(types.InlineKeyboardButton("💎 VIP $100 UNLIMITED", url=link))
            upgrade_text=f"🚀 CURRENT: {level}\nUpgrade: {link}"
        msg=bot.send_message(m.chat.id, upgrade_text, reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "DEPOSIT" in txt_up:
        link=f"{AFFILIATE_LINK}?subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Deposit Now", url=link))
        msg=bot.send_message(m.chat.id, f"💰 Deposit: {link}", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "HOW IT WORKS" in txt_up:
        msg=bot.send_message(m.chat.id, "📜 How it Works - 5 Steps", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "ADMIN PANEL" in txt_up:
        if uid!=OWNER_ID:
            return
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
        markup.add(types.InlineKeyboardButton("👥 Users", callback_data="admin_users"), types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
        msg=bot.send_message(m.chat.id, f"👑 ADMIN PANEL", reply_markup=markup)
        track_msg(m.chat.id, msg)

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid=c.from_user.id
    data=c.data
    chat_id=c.message.chat.id
    ensure_user(uid, c.from_user.username or c.from_user.first_name)
    check_daily(uid)
    if data=="howitworks":
        msg=bot.send_message(chat_id, "How it Works", reply_markup=main_menu())
        track_msg(chat_id, msg)
        return
    if data=="real_15":
        clean_and_track(chat_id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 15", callback_data="manual_real"), types.InlineKeyboardButton("🤖 Auto", callback_data="auto_real"))
        msg=bot.send_message(chat_id, "💹 REAL 15:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data=="otc_30":
        clean_and_track(chat_id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 30", callback_data="manual_otc"), types.InlineKeyboardButton("🤖 Auto 30", callback_data="auto_otc"))
        msg=bot.send_message(chat_id, "🔶 OTC 30:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data=="manual_real":
        send_pairs(chat_id, "real", 0)
    elif data=="manual_otc":
        send_pairs(chat_id, "otc", 0)
    elif data.startswith("pairs_"):
        _, typ, page = data.split("_")
        send_pairs(chat_id, typ, int(page))
    elif data.startswith("pair_"):
        _, typ, pair_name = data.split("_",2)
        pair_name=pair_name.replace("_","/")
        markup=types.InlineKeyboardMarkup(row_width=4)
        markup.add(types.InlineKeyboardButton("M1", callback_data=f"exp_M1_{typ}_{pair_name}"), types.InlineKeyboardButton("M2", callback_data=f"exp_M2_{typ}_{pair_name}"), types.InlineKeyboardButton("M3", callback_data=f"exp_M3_{typ}_{pair_name}"), types.InlineKeyboardButton("M5", callback_data=f"exp_M5_{typ}_{pair_name}"))
        msg=bot.send_message(chat_id, f"📊 {pair_name}\nPick Expiry:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data.startswith("exp_"):
        _, exp, typ, pair_name = data.split("_",3)
        pair_name=pair_name.replace("_","/")
        send_signal_result(chat_id, uid, pair_name, exp, typ)
    elif data.startswith("auto_"):
        typ=data.split("_")[1]
        plist=pairs_real if typ=="real" else pairs_otc
        send_signal_result(chat_id, uid, random.choice(plist), "M1", typ)
    elif data=="next_signal":
        clean_and_track(chat_id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✅ REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        msg=bot.send_message(chat_id, "🔥 Select Market:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data=="win":
        users[uid]["wins"]=users[uid].get("wins",0)+1
        users[uid]["gwr_wins"]=users[uid].get("gwr_wins",0)+1
        users[uid]["streak"]=users[uid].get("streak",0)+1
        users[uid]["loss_streak"]=0
        msg=bot.send_message(chat_id, f"WIN! Streak {users[uid]['streak']}", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="loss":
        users[uid]["losses"]=users[uid].get("losses",0)+1
        users[uid]["gwr_losses"]=users[uid].get("gwr_losses",0)+1
        users[uid]["loss_streak"]=users[uid].get("loss_streak",0)+1
        users[uid]["streak"]=0
        msg=bot.send_message(chat_id, f"LOSS {users[uid]['loss_streak']}", reply_markup=main_menu())
        track_msg(chat_id, msg)

def send_pairs(chat_id, typ, page):
    plist=pairs_real if typ=="real" else pairs_otc
    per=10
    start=page*per
    end=start+per
    markup=types.InlineKeyboardMarkup(row_width=2)
    for p in plist[start:end]:
        markup.add(types.InlineKeyboardButton(p, callback_data=f"pair_{typ}_{p.replace('/','_')}"))
    nav=[]
    if page>0:
        nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"pairs_{typ}_{page-1}"))
    if end<len(plist):
        nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"pairs_{typ}_{page+1}"))
    if nav:
        markup.row(*nav)
    msg=bot.send_message(chat_id, f"Pairs Page {page+1}", reply_markup=markup)
    track_msg(chat_id, msg)

def send_signal_result(chat_id, uid, pair, exp, typ):
    check_daily(uid)
    lvl=get_level(uid)
    if users[uid]["used"]>=users[uid]["limit"]:
        link=f"{AFFILIATE_LINK}?subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 UPGRADE NOW", url=link))
        msg=bot.send_message(chat_id, f"LIMIT HIT {users[uid]['used']}/{users[uid]['limit']}\n{link}", reply_markup=markup)
        track_msg(chat_id, msg)
        return
    users[uid]["used"]+=1
    direction, strength, rsi_label, ema_label=get_signal_with_indicators()
    markup=types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ WIN", callback_data="win"), types.InlineKeyboardButton("❌ LOSS", callback_data="loss"))
    markup.add(types.InlineKeyboardButton("🔥 Next Signal", callback_data="next_signal"))
    text=f"🔥 {lvl}\n📊 {pair}\n📈 {direction} - {strength}\n⏰ Exp {exp}\n📉 {rsi_label}\n📊 {ema_label}\n📊 {users[uid]['used']}/{users[uid]['limit']}"
    msg=bot.send_message(chat_id, text, reply_markup=markup)
    track_msg(chat_id, msg)

@bot.message_handler(commands=['start','admin'])
def start_cmd(m):
    uid=m.from_user.id
    ensure_user(uid, m.from_user.username or m.from_user.first_name)
    check_daily(uid)
    lvl=get_level(uid)
    if lvl=="LOCKED" and uid!=OWNER_ID:
        text, markup=locked_message(uid)
        msg=bot.send_message(m.chat.id, text, reply_markup=markup)
        track_msg(m.chat.id, msg)
        return
    msg=bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}! {lvl}", reply_markup=main_menu())
    track_msg(m.chat.id, msg)

def run_bot():
    print("Bot V13.2.9 FINAL")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port=int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
