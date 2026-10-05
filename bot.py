import os, threading, datetime, random
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 8188622130
AFFILIATE_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

users = {}
last_bot_msgs = {}
pairs_real = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","EUR/JPY","USD/CHF","GBP/JPY","EUR/GBP","AUD/JPY","NZD/USD","EUR/AUD","GBP/AUD","USD/CAD","EUR/CAD","AUD/CAD"]
pairs_otc = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","USD/CHF OTC","GBP/JPY OTC","EUR/GBP OTC","AUD/JPY OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC","USD/CAD OTC","EUR/CAD OTC","AUD/CAD OTC","EUR/NZD OTC","GBP/NZD OTC","AUD/NZD OTC","EUR/CHF OTC","GBP/CHF OTC","AUD/CHF OTC","NZD/JPY OTC","CAD/JPY OTC","CHF/JPY OTC","EUR/JPY OTC","USD/BRL OTC","EUR/BRL OTC","GBP/BRL OTC","USD/INR OTC","EUR/INR OTC"]
MOTIV_WORDS = ["Focus","Patience","Discipline","Control","Calm","Power","Win","Rise","Strong","Believe","Hustle","Grind","Courage","Spirit","Faith","Energy","Vision","Dream","Growth","Success","Warrior","Hunter","Master","Legend"]

def get_level(uid):
    if uid == OWNER_ID: return "VIP"
    d = users.get(uid)
    if not d or not d.get("registered"): return "LOCKED"
    dep = d.get("deposit",0)
    if dep >= 100: return "VIP"
    if dep >= 50: return "PRO"
    if dep >= 20: return "STARTER"
    return "NONE"

def get_limit(level): return {"LOCKED":0,"NONE":5,"STARTER":20,"PRO":100,"VIP":999999}.get(level,0)
def get_wr(level): return {"NONE":"55-65%","STARTER":"65-70%","PRO":"70-80%","VIP":"80-87%"}.get(level,"55-65%")

def check_daily(uid):
    today = datetime.date.today().isoformat()
    if users[uid].get("last_day")!= today:
        users[uid]["last_day"]=today
        users[uid]["used"]=0
        users[uid]["wins"]=0
        users[uid]["losses"]=0
        users[uid]["streak"]=0
        users[uid]["loss_streak"]=0

def ensure_user(uid, username):
    if uid not in users:
        users[uid]={"deposit":0,"registered":False,"used":0,"last_day":datetime.date.today().isoformat(),"username":username,"wins":0,"losses":0,"streak":0,"loss_streak":0,"gwr_wins":0,"gwr_losses":0,"banned":False}
    if "gwr_wins" not in users[uid]: users[uid]["gwr_wins"]=0
    if "gwr_losses" not in users[uid]: users[uid]["gwr_losses"]=0
    if "banned" not in users[uid]: users[uid]["banned"]=False
    users[uid]["username"]=username
    if uid==OWNER_ID:
        users[uid]["deposit"]=100
        users[uid]["registered"]=True

def clean_and_track(chat_id, uid):
    if chat_id in last_bot_msgs:
        for mid in last_bot_msgs[chat_id][:]:
            try: bot.delete_message(chat_id, mid)
            except: pass
    last_bot_msgs[chat_id]=[]

def track_msg(chat_id, msg, is_broadcast=False):
    if is_broadcast: return
    if chat_id not in last_bot_msgs: last_bot_msgs[chat_id]=[]
    last_bot_msgs[chat_id].append(msg.message_id)

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📊 GET SIGNAL"))
    markup.add(types.KeyboardButton("💹 REAL 15"), types.KeyboardButton("🔶 OTC 30"))
    markup.add(types.KeyboardButton("💎 Upgrade"), types.KeyboardButton("💰 Deposit"))
    markup.add(types.KeyboardButton("📈 My Status"), types.KeyboardButton("🎯 GWR"))
    markup.add(types.KeyboardButton("📜 How it Works"), types.KeyboardButton("👑 Admin Panel"))
    return markup

@app.route('/')
def home(): return "V13.2.4 MOTIV UPGRADE - 3 PARTS"

@app.route('/postback')
def postback():
    tid=request.args.get('click_id') or request.args.get('subid')
    dep=request.args.get('sum_deposit') or request.args.get('deposit') or 0
    try: dep=float(dep)
    except: dep=0
    if not tid: return "No ID",400
    try: tid=int(tid)
    except: return "Bad ID",400
    if tid not in users:
        users[tid]={"deposit":0,"registered":False,"used":0,"last_day":datetime.date.today().isoformat(),"username":"Unknown","wins":0,"losses":0,"streak":0,"loss_streak":0,"gwr_wins":0,"gwr_losses":0,"banned":False}
    users[tid]["registered"]=True
    if dep>0:
        users[tid]["deposit"]=max(users[tid].get("deposit",0), dep)
        try: bot.send_message(tid, f"💰 Deposit ${dep} confirmed! Level: {get_level(tid)}", reply_markup=main_menu())
        except: pass
    else:
        try: bot.send_message(tid, f"✅ Registration confirmed! You unlocked 5/day FREE", reply_markup=main_menu())
        except: pass
    return "OK",200

@bot.message_handler(commands=['start'])
def start(m):
    uid=m.from_user.id
    ensure_user(uid, m.from_user.username or m.from_user.first_name)
    if users[uid].get("banned"):
        bot.send_message(m.chat.id, "⛔ You are banned by admin. Contact @WW")
        return
    check_daily(uid)
    level=get_level(uid)
    clean_and_track(m.chat.id, uid)
    if level=="LOCKED":
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Register Now - Unlock 5/day FREE", url=link))
        markup.add(types.InlineKeyboardButton("📜 How it Works", callback_data="howitworks"))
        intro_text = f"🔒 WELCOME TO WW POCKET SIGNALS BOT 🔒\n\n👋 Hello {m.from_user.first_name}!\n\n🚀 Most accurate bot 80-87% WIN RATE!\n\n📌 HOW TO UNLOCK:\n1️⃣ Register 👉 {link}\n2️⃣ Get 5/day FREE\n3️⃣ Deposit to upgrade:\n⚪ NONE $0 - 5/day 55-65%\n🟢 STARTER $20 - 20/day 65-70%\n🔵 PRO $50 - 100/day 70-80%\n💎 VIP $100 - UNLIMITED 80-87%\n\n🔗 YOUR LINK:\n{link}"
        msg=bot.send_message(m.chat.id, intro_text, reply_markup=markup)
        track_msg(m.chat.id, msg)
    else:
        used=users[uid].get("used",0)
        limit=get_limit(level)
        msg=bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}!\n👑 {level} | 🎯 {get_wr(level)} WR\n📊 {used}/{limit if limit<999999 else '∞'} Used\n🏆 Daily W:{users[uid].get('wins',0)} L:{users[uid].get('losses',0)} | GWR W:{users[uid].get('gwr_wins',0)} L:{users[uid].get('gwr_losses',0)}", reply_markup=main_menu())
        track_msg(m.chat.id, msg)@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_buttons(m):
    if users.get(m.from_user.id,{}).get("bcast_wait"): return
    txt=m.text.strip()
    uid=m.from_user.id
    if uid not in users: ensure_user(uid, m.from_user.username or m.from_user.first_name)
    if users[uid].get("banned"):
        bot.send_message(m.chat.id, "⛔ You are banned")
        return
    check_daily(uid)

    if "GET SIGNAL" in txt:
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("💹 REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        msg=bot.send_message(m.chat.id, "🔥 Select Market:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "REAL 15" in txt:
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 15", callback_data="manual_real"), types.InlineKeyboardButton("🤖 Auto", callback_data="auto_real"))
        msg=bot.send_message(m.chat.id, "💹 REAL 15 Market:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "OTC 30" in txt:
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 30", callback_data="manual_otc"), types.InlineKeyboardButton("🤖 Auto 30", callback_data="auto_otc"))
        msg=bot.send_message(m.chat.id, "🔶 OTC 30 Market:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "My Status" in txt:
        level=get_level(uid)
        used=users[uid].get("used",0)
        limit=get_limit(level)
        wins=users[uid].get('wins',0)
        losses=users[uid].get('losses',0)
        msg=bot.send_message(m.chat.id, f"👤 STATUS - DAILY (Resets 00:00)\n👑 {level} 🎯 {get_wr(level)}\n💰 ${users[uid].get('deposit',0)}\n📊 Today: {used}/{limit if limit<999999 else '∞'}\n🏆 Daily W:{wins} L:{losses}\n🔥 Streak:{users[uid].get('streak',0)} Loss Streak:{users[uid].get('loss_streak',0)}", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "GWR" in txt:
        gw=users[uid].get('gwr_wins',0)
        gl=users[uid].get('gwr_losses',0)
        total=gw+gl
        gwr=round((gw/total*100) if total>0 else 0,1)
        msg=bot.send_message(m.chat.id, f"🎯 GWR - LIFETIME (Never Resets)\n🏆 Total Wins: {gw}\n❌ Total Losses: {gl}\n🎯 GWR: {gwr}% ({gw}/{total})\n👑 Level {get_level(uid)}", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "Upgrade" in txt:
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        level=get_level(uid)
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚪ NONE $0 5/day", url=link))
        markup.add(types.InlineKeyboardButton("🟢 STARTER $20 20/day", url=link))
        markup.add(types.InlineKeyboardButton("🔵 PRO $50 100/day POPULAR", url=link))
        markup.add(types.InlineKeyboardButton("💎 VIP $100 UNLIMITED BEST", url=link))
        upgrade_text=(
f"💎💎 STOP TRADING LIKE A BEGINNER! 💎💎\n\n"
f"👋 Hey {m.from_user.first_name}, you are currently {level} with {get_wr(level)} WR — but you deserve MORE!\n\n"
f"🔥 WHY UPGRADE NOW?\n"
f"⚪ NONE $0 — 5/day, 55-65% WR — You are here, limited & struggling!\n"
f"🟢 STARTER $20 — 20/day, 65-70% WR — 4X more signals, start winning!\n"
f"🔵 PRO $50 — 100/day, 70-80% WR — MOST POPULAR! Real traders choose PRO!\n"
f"💎 VIP $100 — UNLIMITED, 80-87% WR — BEST OF BEST! No limits, max profit!\n\n"
f"🚀 Imagine: No more 'Limit reached', no more missing good candles, 80-87% accuracy!\n"
f"💪 PRO & VIP traders make 5X more because they have MORE chances!\n\n"
f"👑 You didn't come this far to stay at {level}! Level up NOW and dominate market!\n\n"
f"🔗 Your personal upgrade link:\n{link}"
        )
        msg=bot.send_message(m.chat.id, upgrade_text, reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "Deposit" in txt:
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Deposit Now", url=link))
        dep_text=(
f"💰💰 READY TO 10X YOUR RESULTS? 💰💰\n\n"
f"🔥 Every $20 you deposit unlocks HIGHER WR & MORE signals!\n"
f"💎 VIP $100 = UNLIMITED 87% WR — No more limits!\n"
f"🚀 Deposit now, upgrade instantly, start crushing market!\n\n"
f"🔗 {link}"
        )
        msg=bot.send_message(m.chat.id, dep_text, reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "How it Works" in txt:
        msg=bot.send_message(m.chat.id, "📜 How it Works:\n1️⃣ Register\n2️⃣ 5/day FREE\n3️⃣ Deposit upgrade\n4️⃣ Status Daily\n5️⃣ GWR Lifetime", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "Admin Panel" in txt or txt.startswith('/admin'):
        if uid!=OWNER_ID:
            msg=bot.send_message(m.chat.id, "⛔ Admin only")
            track_msg(m.chat.id, msg)
            return
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📢 Broadcast (2 Selectors)", callback_data="admin_broadcast"))
        markup.add(types.InlineKeyboardButton("👥 Users", callback_data="admin_users"), types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
        markup.add(types.InlineKeyboardButton("➕ Add User", callback_data="admin_adduser"), types.InlineKeyboardButton("🔍 Search User", callback_data="admin_search"))
        markup.add(types.InlineKeyboardButton("⛔ Ban User", callback_data="admin_ban"), types.InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"))
        msg=bot.send_message(m.chat.id, f"👑 ADMIN PANEL\nTotal: {len(users)}\n✅ Motiv Upgrade + GWR removed from 6 loss", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif txt.startswith('/users') or txt.startswith('/stats') or txt.startswith('/broadcast') or txt.startswith('/adduser') or txt.startswith('/such') or txt.startswith('/search') or txt.startswith('/find') or txt.startswith('/ban') or txt.startswith('/unban'):
        admin_cmd(m)

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid=c.from_user.id
    data=c.data
    chat_id=c.message.chat.id
    ensure_user(uid, c.from_user.username or c.from_user.first_name)
    if users[uid].get("banned"): return
    check_daily(uid)
    if data=="get_signal":
        clean_and_track(chat_id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("💹 REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
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
    elif data=="manual_real": send_pairs(chat_id, "real", 0)
    elif data=="manual_otc": send_pairs(chat_id, "otc", 0)
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
        markup.add(types.InlineKeyboardButton("💹 REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        msg=bot.send_message(chat_id, "🔥 Select Market:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data=="win":
        users[uid]["wins"]=users[uid].get("wins",0)+1
        users[uid]["gwr_wins"]=users[uid].get("gwr_wins",0)+1
        users[uid]["streak"]=users[uid].get("streak",0)+1
        users[uid]["loss_streak"]=0
        msg=bot.send_message(chat_id, f"BOOM! WIN! 🔥 Streak {users[uid]['streak']} | Daily W:{users[uid]['wins']} L:{users[uid]['losses']} | GWR {users[uid]['gwr_wins']}/{users[uid]['gwr_losses']}", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="loss":
        users[uid]["losses"]=users[uid].get("losses",0)+1
        users[uid]["gwr_losses"]=users[uid].get("gwr_losses",0)+1
        users[uid]["loss_streak"]=users[uid].get("loss_streak",0)+1
        users[uid]["streak"]=0
        ls=users[uid]["loss_streak"]
        if ls>=6:
            txt=(
f"⚠️⚠️ MARKET NOT STABLE — STOP NOW! ⚠️⚠️\n\n"
f"💔💔💔 {ls} LOSSES IN A ROW — RED ALERT! 💔💔💔\n\n"
f"🧠 Listen to me {c.from_user.first_name} — the market is NOT in your favor right now. It's choppy, manipulated, and hunting your money!\n\n"
f"☕ TAKE A REAL BREAK — 30 to 60 minutes minimum!\n"
f"🚫 Don't revenge trade! Don't double your lot! Don't chase!\n"
f"💧 Drink water, walk away, breathe, reset your mind.\n\n"
f"📊 Your Stats Today: W:{users[uid]['wins']} L:{users[uid]['losses']}\n\n"
f"👑 Real traders know when to STOP — that's what makes them VIP!\n"
f"🔥 Come back later and we will CRUSH it together!"
            )
        else:
            words=random.sample(MOTIV_WORDS, 3)
            w1,w2,w3=words[0],words[1],words[2]
            long_motiv = [
f"💔 LOSS {ls}/5 — BUT LISTEN {c.from_user.first_name}!\n\n💎 {w1} • {w2} • {w3} 💎\n\n🔥 One loss doesn't define you! Champions are built in moments like this! You are {w1}, you have {w2}, you need {w3} — that's the trader mindset!\n\n⚡ The market tested you, but you are still standing! The next signal is coming, and it's YOUR comeback! Don't quit now, legends never do!\n\n🏆 Daily W:{users[uid]['wins']} L:{users[uid]['losses']} — Keep fighting!",
f"😤 Ouch! Loss {ls} — I feel you {c.from_user.first_name}!\n\n🎯 POWER WORDS: {w1} | {w2} | {w3}\n\n💪 This is where 90% give up and 10% become PRO! Which one are you? You need {w1} to control emotions, {w2} to wait for perfect entry, {w3} to execute like a beast!\n\n🚀 Take a deep breath. Reset. The market owes you NOTHING but your next WIN is loading... Your {w1} will make it happen!\n\n📊 W:{users[uid]['wins']} L:{users[uid]['losses']} — Next one is WIN!",
f"⚠️ LOSS {ls}/5 — WAKE UP CALL!\n\n🔮 {w1} • {w2} • {w3} — Remember these 3 words!\n\n🧘 Every pro trader has been here. What separates you from losers is {w1}! Market is not against you, it's teaching you {w2} and {w3}. Learn, adapt, and strike back harder!\n\n💰 Don't trade angry. Don't trade scared. Trade with {w1} and {w2}. Your VIP signal is waiting — are you ready to dominate?\n\n🔥 Daily: W:{users[uid]['wins']} L:{users[uid]['losses']} | GWR: {users[uid]['gwr_wins']}/{users[uid]['gwr_losses']}",
f"💔 {ls} Losses — But Your Story Isn't Over!\n\n👑 TODAY'S CODE: {w1} - {w2} - {w3}\n\n🌟 {c.from_user.first_name}, real traders lose too! But they never lose {w1}, never lose {w2}, never lose {w3}! That's why you are here, that's why you will win! This loss is fuel, not failure!\n\n🎯 Close your eyes for 10 seconds, say '{w1} {w2} {w3}' and click Next Signal with confidence! The market respects {w1} — show it!\n\n🏆 W:{users[uid]['wins']} L:{users[uid]['losses']} — Legend mode ON!",
f"🔥 LOSS {ls} — PAIN IS TEMPORARY!\n\n💎 {w1} 💎 {w2} 💎 {w3} 💎\n\n⚡ Hear me out {c.from_user.first_name} — You are {w1} enough to handle this! You have {w2} to stay in game! You need {w3} to win next trade! 90% traders quit at loss {ls}, but YOU are different! You are built for PRO level!\n\n🚀 Shake it off! The next candle is yours! Let's turn this red into GREEN!\n\n📈 Daily W:{users[uid]['wins']} L:{users[uid]['losses']} — BOUNCE BACK TIME!"
            ]
            txt=random.choice(long_motiv)
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="admin_users": admin_cmd(c.message, True)
    elif data=="admin_stats": admin_cmd(c.message, True, True)
    elif data=="admin_adduser": bot.send_message(chat_id, "Use: /adduser 123456 50")
    elif data=="admin_search": bot.send_message(chat_id, "Use: /such 123456")
    elif data=="admin_ban": bot.send_message(chat_id, "Use: /ban 123456")
    elif data=="admin_unban": bot.send_message(chat_id, "Use: /unban 123456")
    elif data=="howitworks":
        msg=bot.send_message(chat_id, "📜 How it Works:\n1️⃣ Register\n2️⃣ 5/day FREE\n3️⃣ Deposit upgrade\n4️⃣ Status Daily\n5️⃣ GWR Lifetime", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="admin_broadcast":
        if uid!=OWNER_ID: return
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("📅 1 Day", callback_data="bdel_24"), types.InlineKeyboardButton("📅 1 Week", callback_data="bdel_168"), types.InlineKeyboardButton("📅 1 Month", callback_data="bdel_720"))
        markup.add(types.InlineKeyboardButton("📅 3 Months", callback_data="bdel_2160"), types.InlineKeyboardButton("📅 6 Months", callback_data="bdel_4320"), types.InlineKeyboardButton("📅 1 Year", callback_data="bdel_8760"))
        markup.add(types.InlineKeyboardButton("♾️ Never Delete", callback_data="bdel_0"))
        msg=bot.send_message(chat_id, "⏰ SELECTOR 1/2 - DELETE PERIOD:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data.startswith("bdel_"):
        if uid!=OWNER_ID: return
        hours=int(data.split("_")[1])
        label = {24:"1 Day",168:"1 Week",720:"1 Month",2160:"3 Months",4320:"6 Months",8760:"1 Year",0:"Never"}.get(hours, f"{hours}h")
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("ALL", callback_data=f"bcast_{hours}_ALL"), types.InlineKeyboardButton("NONE", callback_data=f"bcast_{hours}_NONE"), types.InlineKeyboardButton("STARTER", callback_data=f"bcast_{hours}_STARTER"))
        markup.add(types.InlineKeyboardButton("PRO", callback_data=f"bcast_{hours}_PRO"), types.InlineKeyboardButton("VIP", callback_data=f"bcast_{hours}_VIP"))
        msg=bot.send_message(chat_id, f"✅ Selector 1: {label}\n\n👥 SELECTOR 2/2 - TARGET:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data.startswith("bcast_"):
        if uid!=OWNER_ID: return
        _, hours, target = data.split("_")
        users[uid]["bcast_wait"]={"hours":int(hours),"target":target}
        label = {24:"1 Day",168:"1 Week",720:"1 Month",2160:"3 Months",4320:"6 Months",8760:"1 Year",0:"Never"}.get(int(hours), f"{hours}h")
        msg=bot.send_message(chat_id, f"✍️ DONE: Delete {label} | Target {target}\nNow send file")
        track_msg(chat_id, msg)@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'], func=lambda m: users.get(m.from_user.id,{}).get("bcast_wait") is not None and m.from_user.id==OWNER_ID)
def handle_bcast(m):
    uid=m.from_user.id
    wait=users[uid].get("bcast_wait")
    if not wait: return
    hours=wait["hours"]
    target=wait["target"]
    sent=[]
    count=0
    for u_id in list(users.keys()):
        if u_id==OWNER_ID: continue
        lvl=get_level(u_id)
        if target!="ALL" and lvl!=target: continue
        if users[u_id].get("banned"): continue
        try:
            if m.content_type=='text': msg=bot.send_message(u_id, f"📢 ADMIN:\n{m.text}")
            elif m.content_type=='photo': msg=bot.send_photo(u_id, m.photo[-1].file_id, caption=m.caption or "📢 ADMIN")
            elif m.content_type=='video': msg=bot.send_video(u_id, m.video.file_id, caption=m.caption or "📢 ADMIN")
            elif m.content_type=='document': msg=bot.send_document(u_id, m.document.file_id, caption=m.caption or "📢 ADMIN")
            elif m.content_type=='audio': msg=bot.send_audio(u_id, m.audio.file_id, caption=m.caption or "📢 ADMIN")
            elif m.content_type=='voice': msg=bot.send_voice(u_id, m.voice.file_id, caption=m.caption or "📢 ADMIN")
            elif m.content_type=='sticker': msg=bot.send_sticker(u_id, m.sticker.file_id)
            elif m.content_type=='animation': msg=bot.send_animation(u_id, m.animation.file_id, caption=m.caption or "📢 ADMIN")
            elif m.content_type=='video_note': msg=bot.send_video_note(u_id, m.video_note.file_id)
            else: msg=bot.copy_message(u_id, m.chat.id, m.message_id)
            if hours>0: sent.append((u_id, msg.message_id))
            count+=1
        except: pass
    users[uid]["bcast_wait"]=None
    label = {24:"1 Day",168:"1 Week",720:"1 Month",2160:"3 Months",4320:"6 Months",8760:"1 Year",0:"Never"}.get(hours, f"{hours}h")
    msg_confirm=bot.send_message(uid, f"✅ BROADCAST DONE\nType: {m.content_type}\nTarget: {target} = {count}\nDelete: {label}", reply_markup=main_menu())
    track_msg(uid, msg_confirm)
    if hours>0 and sent:
        def auto_del():
            import time
            time.sleep(hours*3600)
            for cid,mid in sent:
                try: bot.delete_message(cid,mid)
                except: pass
        threading.Thread(target=auto_del, daemon=True).start()

def send_pairs(chat_id, typ, page):
    clean_and_track(chat_id, chat_id)
    plist=pairs_real if typ=="real" else pairs_otc
    start=page*10
    end=start+10
    markup=types.InlineKeyboardMarkup(row_width=2)
    for p in plist[start:end]:
        safe=p.replace("/","_")
        markup.add(types.InlineKeyboardButton(p, callback_data=f"pair_{typ}_{safe}"))
    btns=[]
    if end < len(plist): btns.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"pairs_{typ}_{page+1}"))
    if page>0: btns.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"pairs_{typ}_{page-1}"))
    if btns: markup.add(*btns)
    msg=bot.send_message(chat_id, f"Pick pair {typ.upper()} Page {page+1}:", reply_markup=markup)
    track_msg(chat_id, msg)

def send_signal_result(chat_id, uid, pair, exp, typ):
    if get_level(uid)=="LOCKED":
        msg=bot.send_message(chat_id, "🔒 REGISTER FIRST /start")
        track_msg(chat_id, msg)
        return
    check_daily(uid)
    limit=get_limit(get_level(uid))
    used=users[uid].get("used",0)
    if used>=limit and uid!=OWNER_ID:
        msg=bot.send_message(chat_id, f"⛔ Limit {used}/{limit} reached!", reply_markup=main_menu())
        track_msg(chat_id, msg)
        return
    users[uid]["used"]=used+1
    level=get_level(uid)
    action=random.choice(["BUY 📈","SELL 📉"])
    rsi=round(random.uniform(20,80),1)
    trend="Bullish 🔼" if "BUY" in action else "Bearish 🔽"
    wr=get_wr(level)
    markup=types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ WIN", callback_data="win"), types.InlineKeyboardButton("❌ LOSS", callback_data="loss"))
    markup.add(types.InlineKeyboardButton("🔥 Next Signal", callback_data="next_signal"))
    clean_and_track(chat_id, uid)
    msg=bot.send_message(chat_id, f"🔥 {level} {wr} {'💹' if typ=='real' else '🔶'}\n📊 {pair}\n📈 {action}\n⏰ Exp {exp}\n📉 RSI {rsi} {trend}\n📊 {users[uid]['used']}/{limit if limit<999999 else '∞'}", reply_markup=markup)
    track_msg(chat_id, msg)

def admin_cmd(m, is_callback=False, is_stats=False):
    chat_id=m.chat.id
    uid=m.from_user.id if not is_callback else OWNER_ID
    txt=m.text if hasattr(m,'text') else ""
    if uid!=OWNER_ID and not is_callback:
        if "/admin" in txt or "/ban" in txt or "/unban" in txt:
            msg=bot.send_message(chat_id, "⛔ Admin only")
            track_msg(chat_id, msg)
        return
    if is_callback:
        if is_stats:
            c={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
            for u in users: c[get_level(u)]+=1
            msg=bot.send_message(chat_id, f"📊 {c}")
            track_msg(chat_id, msg)
        else:
            out="👥 USERS:\n"
            for uid_,d in list(users.items())[:40]:
                ban="⛔BAN" if d.get("banned") else ""
                out+=f"{uid_} {d.get('username')} {get_level(uid_)} {ban} D:{d.get('wins',0)}/{d.get('losses',0)} G:{d.get('gwr_wins',0)}/{d.get('gwr_losses',0)}\n"
            msg=bot.send_message(chat_id, out)
            track_msg(chat_id, msg)
        return
    if txt.startswith('/users'):
        out="👥 USERS:\n"
        for uid_,d in list(users.items())[:40]:
            ban="⛔BAN" if d.get("banned") else ""
            out+=f"{uid_} {d.get('username')} {get_level(uid_)} {ban} D:{d.get('wins',0)}/{d.get('losses',0)} G:{d.get('gwr_wins',0)}/{d.get('gwr_losses',0)}\n"
        msg=bot.send_message(chat_id, out)
        track_msg(chat_id, msg)
    elif txt.startswith('/stats'):
        c={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for u in users: c[get_level(u)]+=1
        banned=sum(1 for u in users.values() if u.get("banned"))
        msg=bot.send_message(chat_id, f"📊 {c}\n⛔ Banned: {banned}")
        track_msg(chat_id, msg)
    elif txt.startswith('/ban '):
        try:
            uid_ban=int(txt.split()[1])
            if uid_ban not in users:
                msg=bot.send_message(chat_id, f"❌ User {uid_ban} not found")
            else:
                users[uid_ban]["banned"]=True
                msg=bot.send_message(chat_id, f"⛔ Banned {uid_ban} {users[uid_ban].get('username')}")
            track_msg(chat_id, msg)
        except Exception as e:
            msg=bot.send_message(chat_id, f"Usage: /ban 123456\nError {e}")
            track_msg(chat_id, msg)
    elif txt.startswith('/unban '):
        try:
            uid_unban=int(txt.split()[1])
            if uid_unban not in users:
                msg=bot.send_message(chat_id, f"❌ User {uid_unban} not found")
            else:
                users[uid_unban]["banned"]=False
                msg=bot.send_message(chat_id, f"✅ Unbanned {uid_unban}")
            track_msg(chat_id, msg)
        except Exception as e:
            msg=bot.send_message(chat_id, f"Usage: /unban 123456\nError {e}")
            track_msg(chat_id, msg)
    elif txt.startswith('/adduser'):
        try:
            parts=txt.split()
            uid_add=int(parts[1])
            dep=float(parts[2]) if len(parts)>2 else 0
            if uid_add not in users:
                users[uid_add]={"deposit":0,"registered":True,"used":0,"last_day":datetime.date.today().isoformat(),"username":"Added","wins":0,"losses":0,"streak":0,"loss_streak":0,"gwr_wins":0,"gwr_losses":0,"banned":False}
            users[uid_add]["registered"]=True
            users[uid_add]["deposit"]=dep
            msg=bot.send_message(chat_id, f"✅ Added {uid_add} ${dep} {get_level(uid_add)}", reply_markup=main_menu())
            track_msg(chat_id, msg)
        except Exception as e:
            msg=bot.send_message(chat_id, f"Usage: /adduser 123456 50\nError {e}")
            track_msg(chat_id, msg)
    elif txt.startswith('/such') or txt.startswith('/search') or txt.startswith('/find'):
        try:
            uid_search=int(txt.split()[1])
            d=users.get(uid_search)
            if not d:
                msg=bot.send_message(chat_id, f"❌ User {uid_search} not found")
            else:
                check_daily(uid_search)
                msg=bot.send_message(chat_id, f"👤 {uid_search}\nUsername: {d.get('username')}\nLevel: {get_level(uid_search)}\nBanned: {d.get('banned')}\nDaily W:{d.get('wins',0)} L:{d.get('losses',0)}\nGWR W:{d.get('gwr_wins',0)} L:{d.get('gwr_losses',0)}")
            track_msg(chat_id, msg)
        except Exception as e:
            msg=bot.send_message(chat_id, f"Usage: /such 123456\nError {e}")
            track_msg(chat_id, msg)
    elif txt.startswith('/broadcast'):
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("📅 1 Day", callback_data="bdel_24"), types.InlineKeyboardButton("📅 1 Week", callback_data="bdel_168"), types.InlineKeyboardButton("📅 1 Month", callback_data="bdel_720"))
        markup.add(types.InlineKeyboardButton("📅 3 Months", callback_data="bdel_2160"), types.InlineKeyboardButton("📅 6 Months", callback_data="bdel_4320"), types.InlineKeyboardButton("📅 1 Year", callback_data="bdel_8760"))
        markup.add(types.InlineKeyboardButton("♾️ Never", callback_data="bdel_0"))
        msg=bot.send_message(chat_id, "⏰ SELECTOR 1/2 - DELETE PERIOD", reply_markup=markup)
        track_msg(chat_id, msg)

@bot.message_handler(commands=['admin','users','stats','broadcast','adduser','such','search','find','ban','unban'])
def admin_commands(m): admin_cmd(m)

bot.remove_webhook()
print("V13.2.4 FINAL - 3 PARTS DEPLOYED")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

threading.Thread(target=run_flask, daemon=True).start()
bot.infinity_polling()
