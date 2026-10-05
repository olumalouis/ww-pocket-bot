import os, threading, datetime, random
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 8188622130
AFFILIATE_LINK = "https://po.ru/YOUR_LINK"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

users = {}
pairs_real = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","EUR/JPY","USD/CHF","GBP/JPY","EUR/GBP","AUD/JPY","NZD/USD","EUR/AUD","GBP/AUD","USD/CAD","EUR/CAD","AUD/CAD"]
pairs_otc = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","USD/CHF OTC","GBP/JPY OTC","EUR/GBP OTC","AUD/JPY OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC","USD/CAD OTC","EUR/CAD OTC","AUD/CAD OTC","EUR/NZD OTC","GBP/NZD OTC","AUD/NZD OTC","EUR/CHF OTC","GBP/CHF OTC","AUD/CHF OTC","NZD/JPY OTC","CAD/JPY OTC","CHF/JPY OTC","EUR/JPY OTC","USD/BRL OTC","EUR/BRL OTC","GBP/BRL OTC","USD/INR OTC","EUR/INR OTC"]

def get_level(uid):
    if uid == OWNER_ID:
        return "VIP"
    d = users.get(uid)
    if not d or not d.get("registered"):
        return "LOCKED"
    dep = d.get("deposit",0)
    if dep >= 100: return "VIP"
    if dep >= 50: return "PRO"
    if dep >= 20: return "STARTER"
    return "NONE"

def get_limit(level):
    return {"LOCKED":0,"NONE":5,"STARTER":20,"PRO":100,"VIP":999999}.get(level,0)

def get_wr(level):
    return {"NONE":"55-65%","STARTER":"65-70%","PRO":"70-80%","VIP":"80-87%"}.get(level,"55-65%")

def get_limit_text(level):
    return {"NONE":"5/day","STARTER":"20/day","PRO":"100/day","VIP":"Unlimited"}.get(level,"0")

def check_daily(uid):
    today = datetime.date.today().isoformat()
    if users[uid].get("last_day")!= today:
        users[uid]["last_day"] = today
        users[uid]["used"] = 0
        users[uid]["wins"] = 0
        users[uid]["losses"] = 0
        users[uid]["streak"] = 0
        users[uid]["loss_streak"] = 0

def ensure_user(uid, username):
    if uid not in users:
        users[uid] = {"deposit":0,"registered":False,"used":0,"last_day":datetime.date.today().isoformat(),"username":username,"wins":0,"losses":0,"streak":0,"loss_streak":0}
    users[uid]["username"] = username
    if uid == OWNER_ID:
        users[uid]["deposit"] = 100
        users[uid]["registered"] = True

@app.route('/')
def home():
    return "V13.1.4 FINAL LOCKED RUNNING"

@app.route('/postback')
def postback():
    tid = request.args.get('click_id') or request.args.get('subid')
    dep = request.args.get('sum_deposit') or request.args.get('deposit') or 0
    try: dep = float(dep)
    except: dep = 0
    if not tid: return "No ID",400
    try: tid = int(tid)
    except: return "Bad ID",400
    if tid not in users:
        users[tid] = {"deposit":0,"registered":False,"used":0,"last_day":datetime.date.today().isoformat(),"username":"Unknown","wins":0,"losses":0,"streak":0,"loss_streak":0}
    users[tid]["registered"] = True
    if dep > 0:
        users[tid]["deposit"] = max(users[tid].get("deposit",0), dep)
        try: bot.send_message(tid, f"💰 Deposit ${dep} confirmed! Level: {get_level(tid)}")
        except: pass
    else:
        try: bot.send_message(tid, f"✅ Registration confirmed! You unlocked 5/day NONE")
        except: pass
    return "OK",200

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    uname = m.from_user.username or m.from_user.first_name
    ensure_user(uid, uname)
    level = get_level(uid)
    check_daily(uid)
    if level == "LOCKED":
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Register Now - Unlock 5/day", url=link))
        bot.send_message(m.chat.id, "🔒 LOCKED - REGISTER FIRST\n\nRegister via link to unlock signals", reply_markup=markup)
    else:
        used = users[uid].get("used",0)
        limit = get_limit(level)
        remains = limit - used if limit < 999999 else 999
        wr = get_wr(level)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📊 GET SIGNAL", callback_data="get_signal"))
        markup.add(types.InlineKeyboardButton("💹 REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        markup.add(types.InlineKeyboardButton("💎 Upgrade", callback_data="upgrade"), types.InlineKeyboardButton("💰 Deposit", callback_data="deposit"))
        markup.add(types.InlineKeyboardButton("📈 My Status", callback_data="my_status"), types.InlineKeyboardButton("📜 How it Works", callback_data="howitworks"))
        bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}!\n👑 {level} | 🎯 {wr} WR\n📊 {used}/{limit if limit<999999 else '∞'} Used | {remains if remains!=999 else '∞'} Remains", reply_markup=markup)@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid = c.from_user.id
    data = c.data
    chat_id = c.message.chat.id
    ensure_user(uid, c.from_user.username or c.from_user.first_name)
    check_daily(uid)
    level = get_level(uid)

    if data == "get_signal":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("💹 REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        bot.send_message(chat_id, "🔥 Select Market:", reply_markup=markup)

    elif data == "real_15":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 15", callback_data="manual_real"), types.InlineKeyboardButton("🤖 Auto", callback_data="auto_real"))
        bot.send_message(chat_id, "💹 REAL 15 Market:", reply_markup=markup)

    elif data == "otc_30":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✋ Manual 30", callback_data="manual_otc"), types.InlineKeyboardButton("🤖 Auto 30", callback_data="auto_otc"))
        bot.send_message(chat_id, "🔶 OTC 30 Market:", reply_markup=markup)

    elif data == "manual_real":
        send_pairs(chat_id, "real", 0)
    elif data == "manual_otc":
        send_pairs(chat_id, "otc", 0)

    elif data.startswith("pairs_"):
        _, typ, page = data.split("_")
        send_pairs(chat_id, typ, int(page))

    elif data.startswith("pair_"):
        _, typ, pair_name = data.split("_",2)
        pair_name = pair_name.replace("_","/")
        markup = types.InlineKeyboardMarkup(row_width=4)
        markup.add(types.InlineKeyboardButton("M1", callback_data=f"exp_M1_{typ}_{pair_name}"), types.InlineKeyboardButton("M2", callback_data=f"exp_M2_{typ}_{pair_name}"), types.InlineKeyboardButton("M3", callback_data=f"exp_M3_{typ}_{pair_name}"), types.InlineKeyboardButton("M5", callback_data=f"exp_M5_{typ}_{pair_name}"))
        bot.send_message(chat_id, f"📊 {pair_name}\n⏰ Pick Expiry:", reply_markup=markup)

    elif data.startswith("exp_"):
        _, exp, typ, pair_name = data.split("_",3)
        pair_name = pair_name.replace("_","/")
        send_signal_result(chat_id, uid, pair_name, exp, typ)

    elif data.startswith("auto_"):
        typ = data.split("_")[1]
        pair_list = pairs_real if typ == "real" else pairs_otc
        pair = random.choice(pair_list)
        send_signal_result(chat_id, uid, pair, "M1", typ)

    elif data == "next_signal":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("💹 REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
        bot.send_message(chat_id, "🔥 Select Market:", reply_markup=markup)

    elif data == "win":
        users[uid]["wins"] += 1
        users[uid]["streak"] += 1
        users[uid]["loss_streak"] = 0
        bot.send_message(chat_id, f"BOOM! WIN! 🔥 Streak: {users[uid]['streak']} Wins! 🏆 W:{users[uid]['wins']} L:{users[uid]['losses']}")

    elif data == "loss":
        users[uid]["losses"] += 1
        users[uid]["loss_streak"] += 1
        users[uid]["streak"] = 0
        if users[uid]["loss_streak"] >= 6:
            bot.send_message(chat_id, f"☕ {users[uid]['loss_streak']} Losses in row — take 15 min break! 💪\n🏆 W:{users[uid]['wins']} L:{users[uid]['losses']}")
        else:
            bot.send_message(chat_id, f"Don't worry! Next WIN coming 💪\n🏆 W:{users[uid]['wins']} L:{users[uid]['losses']}")

    elif data == "my_status":
        used = users[uid].get("used",0)
        limit = get_limit(level)
        bot.send_message(chat_id, f"👤 STATUS\n👑 Level: {level}\n💰 Deposit: ${users[uid].get('deposit',0)}\n📊 Today: {used}/{limit if limit<999999 else '∞'}\n🏆 W:{users[uid].get('wins',0)} L:{users[uid].get('losses',0)} Streak:{users[uid].get('streak',0)}\n📅 Reset daily 00:00 UTC ✅")

    elif data == "upgrade":
        link = f"{AFFILIATE_LINK}?subid={uid}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚪ NONE $0 5/day 55-65%", url=link))
        markup.add(types.InlineKeyboardButton("🟢 STARTER $20 20/day 65-70%", url=link))
        markup.add(types.InlineKeyboardButton("🔵 PRO $50 100/day 70-80% POPULAR 🔥", url=link))
        markup.add(types.InlineKeyboardButton("💎 VIP $100 UNLIMITED 80-87% BEST", url=link))
        bot.send_message(chat_id, "💎 UPGRADE PLANS:", reply_markup=markup)

    elif data == "deposit":
        link = f"{AFFILIATE_LINK}?subid={uid}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Deposit Now", url=link))
        bot.send_message(chat_id, "💰 Deposit to upgrade:", reply_markup=markup)

    elif data == "howitworks":
        bot.send_message(chat_id, "📜 How it Works:\n1️⃣ Register\n2️⃣ Get 5/day\n3️⃣ Deposit to upgrade\n4️⃣ GET SIGNAL\n5️⃣ WIN/LOSS resets daily")

    elif data == "admin_broadcast":
        if uid!= OWNER_ID: return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⏰ 1 Hour", callback_data="bdel_1"), types.InlineKeyboardButton("⏰ 6 Hours", callback_data="bdel_6"))
        markup.add(types.InlineKeyboardButton("⏰ 12 Hours", callback_data="bdel_12"), types.InlineKeyboardButton("⏰ 24 Hours", callback_data="bdel_24"))
        markup.add(types.InlineKeyboardButton("♾️ Never Delete", callback_data="bdel_0"))
        bot.send_message(chat_id, "⏰ SELECTOR 1 - AUTO DELETE PERIOD:", reply_markup=markup)

    elif data.startswith("bdel_"):
        if uid!= OWNER_ID: return
        hours = int(data.split("_")[1])
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("ALL", callback_data=f"bcast_{hours}_ALL"), types.InlineKeyboardButton("NONE", callback_data=f"bcast_{hours}_NONE"), types.InlineKeyboardButton("STARTER", callback_data=f"bcast_{hours}_STARTER"))
        markup.add(types.InlineKeyboardButton("PRO", callback_data=f"bcast_{hours}_PRO"), types.InlineKeyboardButton("VIP", callback_data=f"bcast_{hours}_VIP"))
        bot.send_message(chat_id, f"✅ Delete: {hours}h\n👥 SELECTOR 2 - SELECT LEVEL:", reply_markup=markup)

    elif data.startswith("bcast_"):
        if uid!= OWNER_ID: return
        _, hours, target = data.split("_")
        hours = int(hours)
        users[uid]["bcast_wait"] = {"hours": hours, "target": target}
        bot.send_message(chat_id, f"✍️ Send NOW for {target} (auto delete {hours}h) - Any file type!")

@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'], func=lambda m: users.get(m.from_user.id,{}).get("bcast_wait") is not None and m.from_user.id==OWNER_ID)
def handle_bcast(m):
    uid = m.from_user.id
    wait = users[uid].get("bcast_wait")
    if not wait: return
    hours = wait["hours"]
    target = wait["target"]
    sent = []
    count = 0
    for u_id in list(users.keys()):
        if u_id == OWNER_ID: continue
        lvl = get_level(u_id)
        if target!= "ALL" and lvl!= target: continue
        try:
            if m.content_type == 'text':
                msg = bot.send_message(u_id, f"📢 ADMIN:\n{m.text}\n⏰ Auto delete: {'Never' if hours==0 else f'{hours}h'}")
            elif m.content_type == 'photo':
                msg = bot.send_photo(u_id, m.photo[-1].file_id, caption=m.caption or f"📢 ADMIN")
            elif m.content_type == 'video':
                msg = bot.send_video(u_id, m.video.file_id, caption=m.caption or f"📢 ADMIN")
            elif m.content_type == 'document':
                msg = bot.send_document(u_id, m.document.file_id, caption=m.caption or f"📢 ADMIN")
            elif m.content_type == 'audio':
                msg = bot.send_audio(u_id, m.audio.file_id, caption=m.caption or f"📢 ADMIN")
            elif m.content_type == 'voice':
                msg = bot.send_voice(u_id, m.voice.file_id, caption=m.caption or f"📢 ADMIN")
            elif m.content_type == 'sticker':
                msg = bot.send_sticker(u_id, m.sticker.file_id)
            elif m.content_type == 'animation':
                msg = bot.send_animation(u_id, m.animation.file_id, caption=m.caption or f"📢 ADMIN")
            elif m.content_type == 'video_note':
                msg = bot.send_video_note(u_id, m.video_note.file_id)
            else:
                msg = bot.copy_message(u_id, m.chat.id, m.message_id)
            if hours > 0: sent.append((u_id, msg.message_id))
            count += 1
        except: pass
    users[uid]["bcast_wait"] = None
    bot.send_message(uid, f"✅ Broadcast {m.content_type} to {target}: {count} users - Delete {hours}h")
    if hours > 0 and sent:
        def auto_del():
            import time
            time.sleep(hours * 3600)
            for cid, mid in sent:
                try: bot.delete_message(cid, mid)
                except: pass
        threading.Thread(target=auto_del, daemon=True).start()

def send_pairs(chat_id, typ, page):
    plist = pairs_real if typ == "real" else pairs_otc
    start = page * 10
    end = start + 10
    markup = types.InlineKeyboardMarkup(row_width=2)
    for p in plist[start:end]:
        safe = p.replace("/","_")
        markup.add(types.InlineKeyboardButton(p, callback_data=f"pair_{typ}_{safe}"))
    btns = []
    if end < len(plist):
        btns.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"pairs_{typ}_{page+1}"))
    if page > 0:
        btns.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"pairs_{typ}_{page-1}"))
    if btns: markup.add(*btns)
    bot.send_message(chat_id, f"Pick pair {typ.upper()} Page {page+1}:", reply_markup=markup)

def send_signal_result(chat_id, uid, pair, exp, typ):
    if get_level(uid) == "LOCKED":
        bot.send_message(chat_id, "🔒 REGISTER FIRST /start")
        return
    check_daily(uid)
    limit = get_limit(get_level(uid))
    used = users[uid].get("used",0)
    if used >= limit and uid!= OWNER_ID:
        bot.send_message(chat_id, f"⛔ Limit {used}/{limit} reached!")
        return
    users[uid]["used"] = used + 1
    level = get_level(uid)
    action = random.choice(["BUY 📈","SELL 📉"])
    rsi = round(random.uniform(20,80),1)
    trend = "Bullish 🔼" if "BUY" in action else "Bearish 🔽"
    wr = get_wr(level)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ WIN", callback_data="win"), types.InlineKeyboardButton("❌ LOSS", callback_data="loss"))
    markup.add(types.InlineKeyboardButton("🔥 Next Signal", callback_data="next_signal"))
    bot.send_message(chat_id, f"🔥 {level} {wr} { '💹' if typ=='real' else '🔶'}\n📊 {pair}\n📈 {action}\n⏰ Exp {exp}\n📉 RSI {rsi} {trend}\n📊 {users[uid]['used']}/{limit if limit<999999 else '∞'}", reply_markup=markup)

@bot.message_handler(commands=['admin','users','stats','broadcast','adduser','such','search','find'])
def admin(m):
    if m.from_user.id!= OWNER_ID: return
    txt = m.text.strip()
    if txt.startswith('/admin'):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📢 Broadcast All Files", callback_data="admin_broadcast"))
        bot.send_message(m.chat.id, f"👑 ADMIN FINAL\nTotal: {len(users)}\n✅ BUY/SELL not CALL/PUT\n✅ Add user + Search user\n✅ W/L daily\n✅ All files + Auto delete", reply_markup=markup)
    elif txt.startswith('/adduser'):
        try:
            parts = txt.split()
            uid_add = int(parts[1])
            dep = float(parts[2]) if len(parts)>2 else 0
            if uid_add not in users:
                users[uid_add] = {"deposit":0,"registered":True,"used":0,"last_day":datetime.date.today().isoformat(),"username":"Added","wins":0,"losses":0,"streak":0,"loss_streak":0}
            users[uid_add]["registered"] = True
            users[uid_add]["deposit"] = dep
            bot.send_message(m.chat.id, f"✅ Added user {uid_add} deposit ${dep} Level {get_level(uid_add)}")
            try: bot.send_message(uid_add, f"✅ You have been added! Level {get_level(uid_add)} - /start")
            except: pass
        except Exception as e:
            bot.send_message(m.chat.id, f"Usage: /adduser 123456 50\nError {e}")
    elif txt.startswith('/such') or txt.startswith('/search') or txt.startswith('/find'):
        try:
            parts = txt.split()
            uid_search = int(parts[1])
            d = users.get(uid_search)
            if not d:
                bot.send_message(m.chat.id, f"❌ User {uid_search} not found")
            else:
                check_daily(uid_search)
                bot.send_message(m.chat.id, f"👤 User {uid_search}\nUsername: {d.get('username')}\nLevel: {get_level(uid_search)}\nDeposit: ${d.get('deposit',0)}\nUsed: {d.get('used',0)}/{get_limit(get_level(uid_search))}\nW:{d.get('wins',0)} L:{d.get('losses',0)} Streak:{d.get('streak',0)} LossStreak:{d.get('loss_streak',0)}\nRegistered: {d.get('registered')}\nLastDay: {d.get('last_day')}")
        except Exception as e:
            bot.send_message(m.chat.id, f"Usage: /such 123456 OR /search 123456\nError {e}")
    elif txt.startswith('/broadcast'):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⏰ 1h", callback_data="bdel_1"), types.InlineKeyboardButton("⏰ 6h", callback_data="bdel_6"))
        markup.add(types.InlineKeyboardButton("⏰ 12h", callback_data="bdel_12"), types.InlineKeyboardButton("⏰ 24h", callback_data="bdel_24"))
        markup.add(types.InlineKeyboardButton("♾️ Never", callback_data="bdel_0"))
        bot.send_message(m.chat.id, "SELECTOR 1 - Auto Delete:", reply_markup=markup)
    elif txt.startswith('/users'):
        out = "👥 USERS:\n"
        for uid,d in list(users.items())[:40]:
            out += f"{uid} {d.get('username')} {get_level(uid)} ${d.get('deposit',0)} W:{d.get('wins',0)} L:{d.get('losses',0)}\n"
        bot.send_message(m.chat.id, out)
    elif txt.startswith('/stats'):
        c = {"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for uid in users: c[get_level(uid)] += 1
        bot.send_message(m.chat.id, f"📊 {c} BUY/SELL ✅")

bot.remove_webhook()
print("V13.1.4 FINAL FIXED - BUY SELL + ADDUSER + SUCH + ALL FILES + AUTO DELETE + DAILY W/L")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

threading.Thread(target=run_flask, daemon=True).start()
bot.infinity_polling()
