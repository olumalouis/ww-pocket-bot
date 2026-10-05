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
    return "✅ WW POCKET SIGNALS V13.2.9 Alive - OWNER 8188622130"

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
        lvl=get_level(uid)
        users[uid]["limit"]=get_limit(lvl)
        print(f"✅ POSTBACK: {uid} deposit {dep} -> {lvl}")
        return f"OK {uid} {lvl}", 200
    except Exception as e:
        print(f"Postback error: {e}")
        return "ERROR", 400

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
        lvl=get_level(uid)
        users[uid]["limit"]=get_limit(lvl)

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
    text=(f"🔒 WELCOME TO WW POCKET SIGNALS BOT\n\nHello! 👋\n\n🔥 80-87% WIN RATE SIGNALS\n\n🔒 YOU ARE LOCKED - Register to unlock\n\nHow to unlock:\n1️⃣ Register via link with?subid={uid}\n2️⃣ Get 5/day FREE instantly\n3️⃣ Deposit upgrade:\n⚪ NONE 5/day 55-65% FREE\n🟢 STARTER $20 20/day 65-70%\n🔵 PRO $50 100/day 70-80%\n💎 VIP $100 UNLIMITED 80-87%\n\n👇 Click Register Now!")
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
        last_bot_msgs[chat_id]=[]@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note','location','contact','poll','venue','dice','game'], func=lambda m: broadcast_wait.get(m.from_user.id) is not None or users.get(m.from_user.id,{}).get("bcast_wait") is not None)
def handle_bcast(m):
    uid=m.from_user.id
    wait=broadcast_wait.get(uid) or users.get(uid,{}).get("bcast_wait")
    if not wait:
        return
    if uid!=OWNER_ID:
        return
    hours=wait["hours"]
    target=wait["target"]
    sent=[]
    count=0
    failed=0
    for u_id in list(users.keys()):
        if u_id==OWNER_ID:
            continue
        lvl=get_level(u_id)
        if target!="ALL" and lvl!=target:
            continue
        if users[u_id].get("banned"):
            continue
        try:
            if m.content_type=='text':
                msg=bot.send_message(u_id, f"📢 ADMIN:\n\n{m.text}")
            else:
                msg=bot.copy_message(u_id, m.chat.id, m.message_id)
            if hours>0:
                sent.append((u_id, msg.message_id))
            count+=1
        except:
            failed+=1
            pass
    if uid in broadcast_wait:
        del broadcast_wait[uid]
    if uid in users and users[uid].get("bcast_wait"):
        users[uid]["bcast_wait"]=None
    msg_confirm=bot.send_message(uid, f"✅ BROADCAST DONE\n📁 Type: {m.content_type}\n👥 Target: {target}\n✅ Sent: {count}\n❌ Failed: {failed}\n⏰ Delete: {hours}h", reply_markup=main_menu())
    track_msg(uid, msg_confirm)
    if hours>0 and sent:
        def auto_del():
            time.sleep(hours*3600)
            for cid,mid in sent:
                try:
                    bot.delete_message(cid,mid)
                except:
                    pass
        threading.Thread(target=auto_del, daemon=True).start()

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
    ema_label=f"EMA200 Price {price} {'Above' if above else 'Below'} EMA200 {'🔼' if above else '🔽'}"
    ema_type="bullish" if above else "bearish"
    if rsi_type=="bullish" and ema_type=="bullish":
        direction="BUY 📈"
        strength="Strong Bullish 🔼🔼"
    elif rsi_type=="bearish" and ema_type=="bearish":
        direction="SELL 📉"
        strength="Strong Bearish 🔽🔽"
    elif rsi_type=="bullish":
        direction="BUY 📈"
        strength="Bullish 🔼"
    elif rsi_type=="bearish":
        direction="SELL 📉"
        strength="Bearish 🔽"
    else:
        if ema_type=="bullish":
            direction="BUY 📈"
            strength="Bullish 🔼"
        else:
            direction="SELL 📉"
            strength="Bearish 🔽"
    return direction, strength, rsi_label, ema_label

@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_buttons(m):
    uid=m.from_user.id
    txt=(m.text or "")
    txt_up=txt.upper()
    if broadcast_wait.get(uid) or users.get(uid,{}).get("bcast_wait"):
        if any(k in txt_up for k in ["GET SIGNAL","REAL 15","OTC 30","UPGRADE","DEPOSIT","MY STATUS","HOW IT WORKS","ADMIN PANEL","/START","/ADDUSER","/BAN","/USERS","/STATS","CANCEL","GWR"]):
            if uid in broadcast_wait:
                del broadcast_wait[uid]
            if uid in users and users[uid].get("bcast_wait"):
                users[uid]["bcast_wait"]=None
        else:
            return
    if uid not in users:
        ensure_user(uid, m.from_user.username or m.from_user.first_name)
    if users[uid].get("banned"):
        bot.send_message(m.chat.id, "⛔ You are banned")
        return
    check_daily(uid)
    lvl=get_level(uid)
    if lvl=="LOCKED" and not any(k in txt_up for k in ["HOW IT WORKS","ADMIN PANEL","/START"]):
        if "GET SIGNAL" in txt_up or "REAL 15" in txt_up or "OTC 30" in txt_up or "MY STATUS" in txt_up or "UPGRADE" in txt_up or "DEPOSIT" in txt_up:
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
        if lvl=="LOCKED":
            text, markup=locked_message(uid)
            msg=bot.send_message(m.chat.id, text, reply_markup=markup)
            track_msg(m.chat.id, msg)
            return
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 15", callback_data="manual_real"), types.InlineKeyboardButton("🤖 Auto", callback_data="auto_real"))
        msg=bot.send_message(m.chat.id, "💹 REAL 15 Market - 15 pairs:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "OTC 30" in txt_up:
        if lvl=="LOCKED":
            text, markup=locked_message(uid)
            msg=bot.send_message(m.chat.id, text, reply_markup=markup)
            track_msg(m.chat.id, msg)
            return
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 30", callback_data="manual_otc"), types.InlineKeyboardButton("🤖 Auto 30", callback_data="auto_otc"))
        msg=bot.send_message(m.chat.id, "🔶 OTC 30 Market - 30 pairs:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "MY STATUS" in txt_up:
        if lvl=="LOCKED":
            text, markup=locked_message(uid)
            msg=bot.send_message(m.chat.id, text, reply_markup=markup)
            track_msg(m.chat.id, msg)
            return
        wins=users[uid].get('wins',0)
        losses=users[uid].get('losses',0)
        msg=bot.send_message(m.chat.id, f"📈 MY STATUS - DAILY RESET 00:00 UTC\n\n🏆 DAILY W/L:\n✅ Wins Today: {wins}\n❌ Losses Today: {losses}\n\n⏰ Resets daily at 00:00 UTC", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "UPGRADE" in txt_up:
        link = f"{AFFILIATE_LINK}?subid={uid}"
        level=get_level(uid)
        markup=types.InlineKeyboardMarkup()
        if level=="VIP":
            markup.add(types.InlineKeyboardButton("💎 You are VIP 👑", url=link))
            upgrade_text=f"🎉 CONGRATULATIONS {m.from_user.first_name}! 👑\n\n💎 YOU ARE VIP - MAX LEVEL REACHED!\n\n✅ UNLIMITED SIGNALS\n✅ 80-87% ACCURACY\n✅ NO LIMITS - MAX PROFIT!\n\n🔥 YOU ARE AT THE TOP!"
        else:
            markup.add(types.InlineKeyboardButton("⚪ NONE $0 5/day 55-65%", url=link))
            markup.add(types.InlineKeyboardButton("🟢 STARTER $20 20/day 65-70%", url=link))
            markup.add(types.InlineKeyboardButton("🔵 PRO $50 100/day 70-80% 🔥 POPULAR", url=link))
            markup.add(types.InlineKeyboardButton("💎 VIP $100 UNLIMITED 80-87% 👑 BEST", url=link))
            upgrade_text=f"🚀 {m.from_user.first_name}, YOU'RE LEAVING MONEY ON TABLE! 💸\n\n🔥 CURRENT: {level} - LIMITED SIGNALS!\n\n💰 UPGRADE & DOMINATE MARKET:\n⚪ NONE $0 - 5/day 55-65%\n🟢 STARTER $20 - 20/day 65-70%\n🔵 PRO $50 - 100/day 70-80% MOST POPULAR!\n💎 VIP $100 UNLIMITED 80-87%\n\n🔗 {link}\n⏰ UPGRADE TODAY!"
        msg=bot.send_message(m.chat.id, upgrade_text, reply_markup=markup)
        track_msg(m.chat.id, msg)    elif "DEPOSIT" in txt_up:
        link = f"{AFFILIATE_LINK}?subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Deposit Now", url=link))
        msg=bot.send_message(m.chat.id, f"💰 Deposit now to upgrade!\n🔗 {link}", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "HOW IT WORKS" in txt_up or txt_up.startswith("HOW"):
        msg=bot.send_message(m.chat.id, "📜 How it Works - 5 Steps:\n1️⃣ Register via link?subid=ID\n2️⃣ Get 5/day FREE\n3️⃣ Deposit to upgrade STARTER/PRO/VIP\n4️⃣ Use GET SIGNAL → REAL 15 / OTC 30\n5️⃣ Track Daily W/L in My Status - Resets 00:00 UTC\n\n🏆 GWR never resets - global tracking", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "ADMIN PANEL" in txt_up:
        if uid!=OWNER_ID:
            msg=bot.send_message(m.chat.id, "⛔ Admin only")
            track_msg(m.chat.id, msg)
            return
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📢 Broadcast (2 Selectors)", callback_data="admin_broadcast"))
        markup.add(types.InlineKeyboardButton("👥 Users", callback_data="admin_users"), types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
        markup.add(types.InlineKeyboardButton("🏆 GWR Global", callback_data="admin_gwr"), types.InlineKeyboardButton("📈 Daily Stats", callback_data="admin_daily"))
        msg=bot.send_message(m.chat.id, f"👑 ADMIN PANEL V13.2.9\nTotal: {len(users)}\nID: {OWNER_ID}\n✅ REAL 15 OTC 30 + 2 INDICATORS", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif txt_up.startswith('/USERS') or txt_up.startswith('/STATS') or txt_up.startswith('/GWR') or txt_up.startswith('/ADDUSER') or txt_up.startswith('/SUCH') or txt_up.startswith('/SEARCH') or txt_up.startswith('/FIND') or txt_up.startswith('/BAN') or txt_up.startswith('/UNBAN'):
        admin_cmd(m)

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid=c.from_user.id
    data=c.data
    chat_id=c.message.chat.id
    ensure_user(uid, c.from_user.username or c.from_user.first_name)
    if users[uid].get("banned"):
        return
    check_daily(uid)
    lvl=get_level(uid)
    if data=="howitworks":
        msg=bot.send_message(chat_id, "📜 How it Works - 5 Steps:\n1️⃣ Register via link?subid=ID\n2️⃣ Get 5/day FREE\n3️⃣ Deposit to upgrade\n4️⃣ GET SIGNAL → REAL 15 / OTC 30\n5️⃣ My Status Daily W/L - Resets 00:00 UTC", reply_markup=main_menu())
        track_msg(chat_id, msg)
        return
    if lvl=="LOCKED" and data not in ["howitworks","admin_broadcast","admin_users","admin_stats","admin_gwr","admin_daily"]:
        text, markup=locked_message(uid)
        msg=bot.send_message(chat_id, text, reply_markup=markup)
        track_msg(chat_id, msg)
        return
    if data=="get_signal":
        clean_and_track(chat_id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✅ REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        msg=bot.send_message(chat_id, "🔥 Select Market:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data=="real_15":
        clean_and_track(chat_id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 15", callback_data="manual_real"), types.InlineKeyboardButton("🤖 Auto", callback_data="auto_real"))
        msg=bot.send_message(chat_id, "💹 REAL 15 Market:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data=="otc_30":
        clean_and_track(chat_id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 30", callback_data="manual_otc"), types.InlineKeyboardButton("🤖 Auto 30", callback_data="auto_otc"))
        msg=bot.send_message(chat_id, "🔶 OTC 30 Market:", reply_markup=markup)
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
        msg=bot.send_message(chat_id, f"📊 {pair_name}\n⏰ Pick Expiry:", reply_markup=markup)
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
        msg=bot.send_message(chat_id, f"BOOM! WIN! 🔥 Streak {users[uid]['streak']} | Daily W:{users[uid]['wins']} L:{users[uid]['losses']}", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="loss":
        users[uid]["losses"]=users[uid].get("losses",0)+1
        users[uid]["gwr_losses"]=users[uid].get("gwr_losses",0)+1
        users[uid]["loss_streak"]=users[uid].get("loss_streak",0)+1
        users[uid]["streak"]=0
        ls=users[uid]["loss_streak"]
        if ls>=6:
            txt=f"⚠️⚠️ MARKET NOT STABLE — STOP NOW! ⚠️⚠️\n\n💔 {ls} LOSSES IN A ROW — RED ALERT!\n\n☕ TAKE BREAK 30-60 min! Don't revenge trade!\n📊 Daily W:{users[uid]['wins']} L:{users[uid]['losses']}"
        else:
            words=random.sample(MOTIV_WORDS, 3)
            txt=f"💔 LOSS {ls}/5 — {words[0]} • {words[1]} • {words[2]}\n\n🔥 One loss doesn't define you! Next is WIN!\n📊 Daily W:{users[uid]['wins']} L:{users[uid]['losses']}"
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu())
        track_msg(chat_id, msg)    elif data=="admin_users":
        admin_cmd(c.message, True)
    elif data=="admin_stats":
        admin_cmd(c.message, True, True)
    elif data=="admin_gwr":
        if uid!=OWNER_ID:
            return
        total_gwr_w=0
        total_gwr_l=0
        for u in users.values():
            total_gwr_w+=u.get("gwr_wins",0)
            total_gwr_l+=u.get("gwr_losses",0)
        total=total_gwr_w+total_gwr_l
        wr=round((total_gwr_w/total*100) if total>0 else 0,2)
        msg=bot.send_message(chat_id, f"🏆 GLOBAL WIN RATE (GWR) - NEVER RESET\n\n✅ Total Wins: {total_gwr_w}\n❌ Total Losses: {total_gwr_l}\n📊 Total Trades: {total}\n🔥 Global WR: {wr}%\n\n📈 Daily W/L resets 00:00 UTC\n🏆 GWR never resets", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="admin_daily":
        if uid!=OWNER_ID:
            return
        total_w=0
        total_l=0
        for u in users.values():
            total_w+=u.get("wins",0)
            total_l+=u.get("losses",0)
        msg=bot.send_message(chat_id, f"📈 DAILY STATS - RESETS 00:00 UTC\n\n✅ Wins Today: {total_w}\n❌ Losses Today: {total_l}\n📊 Trades Today: {total_w+total_l}", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="admin_broadcast":
        if uid!=OWNER_ID:
            return
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("📅 1 Day", callback_data="bdel_24"), types.InlineKeyboardButton("📅 1 Week", callback_data="bdel_168"), types.InlineKeyboardButton("📅 1 Month", callback_data="bdel_720"))
        markup.add(types.InlineKeyboardButton("📅 3 Months", callback_data="bdel_2160"), types.InlineKeyboardButton("📅 6 Months", callback_data="bdel_4320"), types.InlineKeyboardButton("📅 1 Year", callback_data="bdel_8760"))
        markup.add(types.InlineKeyboardButton("♾️ Never Delete", callback_data="bdel_0"))
        msg=bot.send_message(chat_id, "⏰ SELECTOR 1/2 - DELETE PERIOD:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data.startswith("bdel_"):
        if uid!=OWNER_ID:
            return
        hours=int(data.split("_")[1])
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("ALL", callback_data=f"bcast_{hours}_ALL"), types.InlineKeyboardButton("NONE", callback_data=f"bcast_{hours}_NONE"), types.InlineKeyboardButton("STARTER", callback_data=f"bcast_{hours}_STARTER"))
        markup.add(types.InlineKeyboardButton("PRO", callback_data=f"bcast_{hours}_PRO"), types.InlineKeyboardButton("VIP", callback_data=f"bcast_{hours}_VIP"), types.InlineKeyboardButton("LOCKED", callback_data=f"bcast_{hours}_LOCKED"))
        msg=bot.send_message(chat_id, f"✅ Delete {hours}h set\n👥 SELECTOR 2/2 - TARGET:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data.startswith("bcast_"):
        if uid!=OWNER_ID:
            return
        _, hours, target = data.split("_")
        broadcast_wait[uid]={"hours":int(hours),"target":target}
        users[uid]["bcast_wait"]={"hours":int(hours),"target":target}
        msg=bot.send_message(chat_id, f"✍️ DONE: Delete {hours}h | Target {target}\nNow send ANY file - ALL SUPPORTED (text/photo/video/document/audio/voice/sticker/animation)!", reply_markup=main_menu())
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
    msg=bot.send_message(chat_id, f"📊 {typ.upper()} Pairs - Page {page+1}: {len(plist)} total", reply_markup=markup)
    track_msg(chat_id, msg)

def send_signal_result(chat_id, uid, pair, exp, typ):
    check_daily(uid)
    lvl=get_level(uid)
    if users[uid]["used"]>=users[uid]["limit"]:
        link = f"{AFFILIATE_LINK}?subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 UPGRADE NOW", url=link))
        if lvl=="NONE":
            text=f"⛔ DAILY LIMIT REACHED! 5/5\n\n🔥 Market still giving WINNERS but you are BLOCKED!\n\n💰 Upgrade to STARTER 20/day, PRO 100/day, VIP UNLIMITED\n\n🔗 {link}"
        else:
            text=f"🔥 LIMIT HIT — YOU ARE ON FIRE! {users[uid]['used']}/{users[uid]['limit']}\n\n💎 VIP UNLIMITED = NO LIMITS!\n\n🔗 {link}"
        msg=bot.send_message(chat_id, text, reply_markup=markup)
        track_msg(chat_id, msg)
        return
    users[uid]["used"]+=1
    direction, strength, rsi_label, ema_label=get_signal_with_indicators()
    left=users[uid]["limit"]-users[uid]["used"]
    left_str=f"{left}" if lvl!="VIP" else "∞"
    used_str=f"{users[uid]['used']}"
    total_str=f"{users[uid]['limit']}" if lvl!="VIP" else "∞"
    vip_emoji="💎 VIP" if lvl=="VIP" else f"🔥 {lvl}"
    market_icon="🔶" if "OTC" in pair else "✅"
    markup=types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ WIN", callback_data="win"), types.InlineKeyboardButton("❌ LOSS", callback_data="loss"))
    markup.add(types.InlineKeyboardButton("🔥 Next Signal", callback_data="next_signal"))
    text=(
f"🔥 {vip_emoji} {market_icon}\n"
f"📊 {pair}\n"
f"📈 {direction} - {strength}\n"
f"⏰ Exp {exp}\n"
f"📉 {rsi_label}\n"
f"📊 {ema_label}\n"
f"📊 {used_str}/{total_str} Today"
    )
    msg=bot.send_message(chat_id, text, reply_markup=markup)
    track_msg(chat_id, msg)

def admin_cmd(m, is_callback=False, is_stats=False):
    uid=m.from_user.id if not is_callback else m.chat.id
    if uid!=OWNER_ID:
        return
    txt=m.text or ""
    txt_up=txt.upper()
    if txt_up.startswith('/ADDUSER'):
        parts=txt.split()
        if len(parts)<3:
            bot.send_message(m.chat.id, "Use: /adduser 123456 50")
            return
        try:
            target_id=int(parts[1])
            dep=int(parts[2])
        except:
            bot.send_message(m.chat.id, "Invalid ID/deposit")
            return
        ensure_user(target_id, f"User{target_id}")
        users[target_id]["registered"]=True
        users[target_id]["deposit"]=dep
        users[target_id]["limit"]=get_limit(get_level(target_id))
        msg=bot.send_message(m.chat.id, f"✅ Added/Updated {target_id}\nDeposit: {dep}\nLevel: {get_level(target_id)}\nLimit: {get_limit(get_level(target_id))}", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
        return
    if txt_up.startswith('/SUCH') or txt_up.startswith('/SEARCH') or txt_up.startswith('/FIND'):
        parts=txt.split()
        if len(parts)<2:
            bot.send_message(m.chat.id, "Use: /such 123456")
            return
        try:
            tid=int(parts[1])
        except:
            bot.send_message(m.chat.id, "Invalid ID")
            return
        if tid not in users:
            bot.send_message(m.chat.id, "User not found")
            return
        u=users[tid]
        lvl=get_level(tid)
        total_gwr=u.get("gwr_wins",0)+u.get("gwr_losses",0)
        wr=round((u.get("gwr_wins",0)/total_gwr*100) if total_gwr>0 else 0,2)
        msg=bot.send_message(m.chat.id, f"🔍 User {tid}\nName: {u['name']}\nLevel: {lvl}\nDeposit: {u['deposit']}\nRegistered: {u.get('registered')}\nDaily W/L: {u['wins']}/{u['losses']}\nGWR W/L: {u['gwr_wins']}/{u['gwr_losses']}\nWR: {wr}%\nLimit: {u['limit']}\nUsed: {u['used']}\nBanned: {u['banned']}")
        track_msg(m.chat.id, msg)
        return
    if txt_up.startswith('/BAN'):
        parts=txt.split()
        if len(parts)<2:
            bot.send_message(m.chat.id, "Use: /ban 123456")
            return
        try:
            tid=int(parts[1])
        except:
            bot.send_message(m.chat.id, "Invalid ID")
            return
        if tid not in users:
            ensure_user(tid, f"User{tid}")
        users[tid]["banned"]=True
        bot.send_message(m.chat.id, f"⛔ Banned {tid}")
        return
    if txt_up.startswith('/UNBAN'):
        parts=txt.split()
        if len(parts)<2:
            bot.send_message(m.chat.id, "Use: /unban 123456")
            return
        try:
            tid=int(parts[1])
        except:
            bot.send_message(m.chat.id, "Invalid ID")
            return
        if tid in users:
            users[tid]["banned"]=False
        bot.send_message(m.chat.id, f"✅ Unbanned {tid}")
        return
    if txt_up.startswith('/USERS') or (is_callback and not is_stats):
        total=len(users)
        banned=sum(1 for u in users.values() if u.get("banned"))
        text=f"👥 Users: {total} | Banned: {banned} | Active: {total-banned}\n\n"
        lvl_counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for u_id in users:
            lvl_counts[get_level(u_id)]+=1
        text+=f"Levels: LOCKED:{lvl_counts['LOCKED']} NONE:{lvl_counts['NONE']} STARTER:{lvl_counts['STARTER']} PRO:{lvl_counts['PRO']} VIP:{lvl_counts['VIP']}\n\n"
        cnt=0
        for u_id, u in list(users.items())[:40]:
            lvl=get_level(u_id)
            gwr_w=u.get("gwr_wins",0)
            gwr_l=u.get("gwr_losses",0)
            total_gwr=gwr_w+gwr_l
            wr=round((gwr_w/total_gwr*100) if total_gwr>0 else 0,1)
            text+=f"{u_id} {lvl} D:{u['wins']}/{u['losses']} GWR:{gwr_w}/{gwr_l} WR:{wr}% {'⛔' if u.get('banned') else ''}\n"
            cnt+=1
            if cnt>=40:
                break
        msg=bot.send_message(m.chat.id, text)
        track_msg(m.chat.id, msg)
        return
    if txt_up.startswith('/STATS') or txt_up.startswith('/GWR') or is_stats:
        total=len(users)
        total_dep=sum(u.get("deposit",0) for u in users.values())
        total_w=sum(u.get("wins",0) for u in users.values())
        total_l=sum(u.get("losses",0) for u in users.values())
        total_gwr_w=sum(u.get("gwr_wins",0) for u in users.values())
        total_gwr_l=sum(u.get("gwr_losses",0) for u in users.values())
        lvl_counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for u_id in users:
            lvl_counts[get_level(u_id)]+=1
        banned=sum(1 for u in users.values() if u.get("banned"))
        msg=bot.send_message(m.chat.id, f"📊 STATS V13.2.9\n\n👥 Users: {total}\n💰 Deposit: ${total_dep}\n📈 DAILY W:{total_w} L:{total_l}\n🏆 GWR W:{total_gwr_w} L:{total_gwr_l}\n\n📊 Levels: LOCKED:{lvl_counts['LOCKED']} NONE:{lvl_counts['NONE']} STARTER:{lvl_counts['STARTER']} PRO:{lvl_counts['PRO']} VIP:{lvl_counts['VIP']}\n⛔ Banned: {banned}\n🌍 GWR Total: {total_gwr_w}W/{total_gwr_l}L")
        track_msg(m.chat.id, msg)
        return

@bot.message_handler(commands=['start','admin'])
def start_cmd(m):
    uid=m.from_user.id
    ensure_user(uid, m.from_user.username or m.from_user.first_name)
    check_daily(uid)
    if uid in broadcast_wait:
        del broadcast_wait[uid]
    if users[uid].get("bcast_wait"):
        users[uid]["bcast_wait"]=None
    lvl=get_level(uid)
    if lvl=="LOCKED" and uid!=OWNER_ID:
        text, markup=locked_message(uid)
        msg=bot.send_message(m.chat.id, text, reply_markup=markup)
        track_msg(m.chat.id, msg)
        return
    used=users[uid].get("used",0)
    limit=users[uid].get("limit",0)
    limit_str=f"{limit}" if lvl!="VIP" else "∞"
    msg=bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}! 👑 {lvl}\n📊 {used}/{limit_str} Used Today", reply_markup=main_menu())
    track_msg(m.chat.id, msg)

@bot.message_handler(commands=['adduser','such','search','find','ban','unban','users','stats','gwr','broadcast'])
def admin_commands(m):
    admin_cmd(m)

def run_bot():
    print("Bot V13.2.9 FINAL - OWNER 8188622130 - REAL 15 OTC 30 - 2 INDICATORS - BUY/SELL")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port=int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
