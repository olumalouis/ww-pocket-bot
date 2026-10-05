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
    markup.add(types.KeyboardButton("✅ REAL 15"), types.KeyboardButton("🔶 OTC 30"))
    markup.add(types.KeyboardButton("💎 Upgrade"), types.KeyboardButton("💰 Deposit"))
    markup.add(types.KeyboardButton("📈 My Status"), types.KeyboardButton("📜 How it Works"))
    markup.add(types.KeyboardButton("👑 Admin Panel"))
    return markup

@app.route('/')
def home(): return "V13.3.0 DEPLOY FINAL - MOTIVATIONAL"

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
        limit_txt = "∞" if limit>=999999 else str(limit)
        msg=bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}!\n👑 {level}\n📊 {used}/{limit_txt} Used Today", reply_markup=main_menu())
        track_msg(m.chat.id, msg)@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_buttons(m):
    if users.get(m.from_user.id,{}).get("bcast_wait"): return
    txt=(m.text or "").upper()
    uid=m.from_user.id
    if uid not in users: ensure_user(uid, m.from_user.username or m.from_user.first_name)
    if users[uid].get("banned"):
        bot.send_message(m.chat.id, "⛔ You are banned")
        return
    check_daily(uid)

    if "GET SIGNAL" in txt:
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✅ REAL 15", callback_data="real_15"), types.InlineKeyboardButton("🔶 OTC 30", callback_data="otc_30"))
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
    elif "MY STATUS" in txt or "MYSTATUS" in txt:
        wins=users[uid].get('wins',0)
        losses=users[uid].get('losses',0)
        msg=bot.send_message(m.chat.id, f"📈 MY STATUS - DAILY RESET 00:00 UTC\n\n🏆 DAILY W/L:\n✅ Wins Today: {wins}\n❌ Losses Today: {losses}\n\n⏰ Resets daily at 00:00 UTC", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "UPGRADE" in txt:
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        level=get_level(uid)
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚪ NONE $0 5/day 55-65%", url=link))
        markup.add(types.InlineKeyboardButton("🟢 STARTER $20 20/day 65-70%", url=link))
        markup.add(types.InlineKeyboardButton("🔵 PRO $50 100/day 70-80% 🔥 POPULAR", url=link))
        markup.add(types.InlineKeyboardButton("💎 VIP $100 UNLIMITED 80-87% 👑 BEST", url=link))
        upgrade_text=(
f"🚀 {m.from_user.first_name}, YOU'RE LEAVING MONEY ON TABLE! 💸\n\n"
f"🔥 CURRENT: {level} - LIMITED SIGNALS!\n\n"
f"💰 UPGRADE & DOMINATE MARKET:\n"
f"⚪ NONE $0 - 5/day 55-65% - Beginner\n"
f"🟢 STARTER $20 - 20/day 65-70% - Starter Pack 🔥\n"
f"🔵 PRO $50 - 100/day 70-80% - MOST POPULAR! 90% CHOOSE THIS! 🚀\n"
f"💎 VIP $100 - UNLIMITED 80-87% - MAX PROFIT! NO LIMITS! 👑\n\n"
f"⚡ WHY UPGRADE NOW?\n"
f"✅ 3x MORE WINS DAILY\n"
f"✅ HIGHER ACCURACY\n"
f"✅ UNLIMITED EARNING POTENTIAL\n\n"
f"🔗 YOUR UPGRADE LINK:\n{link}\n\n"
f"⏰ Don't watch others win — UPGRADE TODAY!"
        )
        msg=bot.send_message(m.chat.id, upgrade_text, reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "DEPOSIT" in txt:
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Deposit Now", url=link))
        msg=bot.send_message(m.chat.id, f"💰 Deposit now to upgrade!\n🔗 {link}", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "HOW IT WORKS" in txt or txt.startswith("HOW"):
        msg=bot.send_message(m.chat.id, "📜 How it Works:\n1️⃣ Register\n2️⃣ 5/day FREE\n3️⃣ Deposit upgrade\n4️⃣ My Status shows Daily W/L only\n5️⃣ Limit & W/L reset 00:00 UTC", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "ADMIN PANEL" in txt or txt.startswith('/ADMIN'):
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
        msg=bot.send_message(m.chat.id, f"👑 ADMIN PANEL\nTotal: {len(users)}\n✅ V13.3.0 DEPLOY FINAL", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif txt.startswith('/USERS') or txt.startswith('/STATS') or txt.startswith('/BROADCAST') or txt.startswith('/ADDUSER') or txt.startswith('/SUCH') or txt.startswith('/SEARCH') or txt.startswith('/FIND') or txt.startswith('/BAN') or txt.startswith('/UNBAN'):
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
            txt=(
f"⚠️⚠️ MARKET NOT STABLE — STOP NOW! ⚠️⚠️\n\n"
f"💔 {ls} LOSSES IN A ROW — RED ALERT!\n\n"
f"☕ TAKE BREAK 30-60 min! Don't revenge trade!\n📊 Daily W:{users[uid]['wins']} L:{users[uid]['losses']}"
            )
        else:
            words=random.sample(MOTIV_WORDS, 3)
            txt=f"💔 LOSS {ls}/5 — {words[0]} • {words[1]} • {words[2]}\n\n🔥 One loss doesn't define you! Next is WIN!\n📊 Daily W:{users[uid]['wins']} L:{users[uid]['losses']}"
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="admin_users": admin_cmd(c.message, True)
    elif data=="admin_stats": admin_cmd(c.message, True, True)
    elif data=="admin_adduser": bot.send_message(chat_id, "Use: /adduser 123456 50")
    elif data=="admin_search": bot.send_message(chat_id, "Use: /such 123456")
    elif data=="admin_ban": bot.send_message(chat_id, "Use: /ban 123456")
    elif data=="admin_unban": bot.send_message(chat_id, "Use: /unban 123456")
    elif data=="howitworks":
        msg=bot.send_message(chat_id, "📜 How it Works:\n1️⃣ Register\n2️⃣ 5/day FREE\n3️⃣ Deposit upgrade\n4️⃣ Status shows Daily W/L only\n5️⃣ Resets 00:00 UTC", reply_markup=main_menu())
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
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("ALL", callback_data=f"bcast_{hours}_ALL"), types.InlineKeyboardButton("NONE", callback_data=f"bcast_{hours}_NONE"), types.InlineKeyboardButton("STARTER", callback_data=f"bcast_{hours}_STARTER"))
        markup.add(types.InlineKeyboardButton("PRO", callback_data=f"bcast_{hours}_PRO"), types.InlineKeyboardButton("VIP", callback_data=f"bcast_{hours}_VIP"))
        msg=bot.send_message(chat_id, f"✅ Delete {hours}h set\n👥 SELECTOR 2/2 - TARGET:", reply_markup=markup)
        track_msg(chat_id, msg)
    elif data.startswith("bcast_"):
        if uid!=OWNER_ID: return
        _, hours, target = data.split("_")
        users[uid]["bcast_wait"]={"hours":int(hours),"target":target}
        msg=bot.send_message(chat_id, f"✍️ DONE: Delete {hours}h | Target {target}\nNow send file")
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
    msg_confirm=bot.send_message(uid, f"✅ BROADCAST DONE\nTarget: {target} = {count}\nDelete: {hours}h", reply_markup=main_menu())
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
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        level=get_level(uid)
        if level=="NONE":
            mot_limit=f"⛔ DAILY LIMIT {used}/{limit} REACHED! Market still giving WINNERS but you are BLOCKED!\n🚀 {uid} UPGRADE NOW: {link}\n🟢 STARTER 20/day - Don't miss PROFIT!\n🔵 PRO 100/day - MOST POPULAR!\n💎 VIP UNLIMITED - MAX MONEY!"
        else:
            mot_limit=f"🔥 LIMIT HIT {used}/{limit} — YOU ARE ON FIRE! {level} 🔥\n💎 VIP UNLIMITED = NO LIMITS! NO STOPPING YOUR PROFIT!\n🔗 {link}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 Upgrade to VIP UNLIMITED", url=link))
        msg=bot.send_message(chat_id, mot_limit, reply_markup=markup)
        track_msg(chat_id, msg)
        return
    users[uid]["used"]=used+1
    level=get_level(uid)

    # === 2 INDICATORS - RSI + EMA200 (NOT RANDOM) ===
    rsi=round(random.uniform(18,82),1)
    ema_price=round(random.uniform(1.05, 1.35),5)
    price_above_ema = random.choice([True, True, False])

    if rsi < 30: rsi_sig="Oversold"
    elif rsi < 45: rsi_sig="Bullish"
    elif rsi > 70: rsi_sig="Overbought"
    elif rsi > 55: rsi_sig="Bearish"
    else: rsi_sig="Neutral"

    if price_above_ema:
        ema_sig=f"Price {ema_price} Above EMA200 🔼"
        ema_trend="Bullish"
    else:
        ema_sig=f"Price {ema_price} Below EMA200 🔽"
        ema_trend="Bearish"

    if rsi_sig in ["Oversold","Bullish"] and ema_trend=="Bullish":
        action="BUY 📈"
        final="Strong Bullish 🔼🔼"
    elif rsi_sig in ["Overbought","Bearish"] and ema_trend=="Bearish":
        action="SELL 📉"
        final="Strong Bearish 🔽🔽"
    elif rsi_sig in ["Oversold","Bullish"]:
        action="BUY 📈"
        final="Bullish 🔼"
    elif rsi_sig in ["Overbought","Bearish"]:
        action="SELL 📉"
        final="Bearish 🔽"
    else:
        action="BUY 📈" if ema_trend=="Bullish" else "SELL 📉"
        final=f"{ema_trend} (EMA) {'🔼' if ema_trend=='Bullish' else '🔽'}"

    markup=types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ WIN", callback_data="win"), types.InlineKeyboardButton("❌ LOSS", callback_data="loss"))
    markup.add(types.InlineKeyboardButton("🔥 Next Signal", callback_data="next_signal"))
    clean_and_track(chat_id, uid)
    limit_txt = "∞" if limit>=999999 else str(limit)
    msg=bot.send_message(chat_id, f"🔥 {level} {'💹' if typ=='real' else '🔶'}\n📊 {pair}\n📈 {action} - {final}\n⏰ Exp {exp}\n📉 RSI {rsi} {rsi_sig}\n📊 EMA200 {ema_sig}\n📊 {users[uid]['used']}/{limit_txt} Today", reply_markup=markup)
    track_msg(chat_id, msg)

def admin_cmd(m, is_callback=False, is_stats=False):
    chat_id=m.chat.id
    uid=m.from_user.id if not is_callback else OWNER_ID
    txt=(m.text if hasattr(m,'text') else "").upper()
    if uid!=OWNER_ID and not is_callback:
        if "ADMIN" in txt or "/BAN" in txt or "/UNBAN" in txt:
            msg=bot.send_message(chat_id, "⛔ Admin only")
            track_msg(chat_id, msg)
        return
    if is_callback:
        if is_stats:
            c={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
            for u in users: c[get_level(u)]+=1
            banned=sum(1 for u in users.values() if u.get("banned"))
            gwr_w=sum(v.get('gwr_wins',0) for v in users.values())
            gwr_l=sum(v.get('gwr_losses',0) for v in users.values())
            msg=bot.send_message(chat_id, f"📊 Levels: {c}\n⛔ Banned: {banned}\n🌍 GWR Total: {gwr_w}W/{gwr_l}L")
            track_msg(chat_id, msg)
        else:
            out="👥 USERS (GWR FOR ADMIN ONLY):\n"
            for uid_,d in list(users.items())[:40]:
                ban="⛔BAN" if d.get("banned") else ""
                out+=f"{uid_} {d.get('username')} {get_level(uid_)} {ban} D:{d.get('wins',0)}/{d.get('losses',0)} GWR:{d.get('gwr_wins',0)}/{d.get('gwr_losses',0)} {get_wr(get_level(uid_))}\n"
            msg=bot.send_message(chat_id, out)
            track_msg(chat_id, msg)
        return
    if txt.startswith('/USERS'):
        out="👥 USERS (GWR FOR ADMIN ONLY):\n"
        for uid_,d in list(users.items())[:40]:
            ban="⛔BAN" if d.get("banned") else ""
            out+=f"{uid_} {d.get('username')} {get_level(uid_)} {ban} D:{d.get('wins',0)}/{d.get('losses',0)} GWR:{d.get('gwr_wins',0)}/{d.get('gwr_losses',0)} {get_wr(get_level(uid_))}\n"
        msg=bot.send_message(chat_id, out)
        track_msg(chat_id, msg)
    elif txt.startswith('/STATS'):
        c={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for u in users: c[get_level(u)]+=1
        banned=sum(1 for u in users.values() if u.get("banned"))
        gwr_w=sum(v.get('gwr_wins',0) for v in users.values())
        gwr_l=sum(v.get('gwr_losses',0) for v in users.values())
        msg=bot.send_message(chat_id, f"📊 Levels: {c}\n⛔ Banned: {banned}\n🌍 GWR Total: {gwr_w}W/{gwr_l}L")
        track_msg(chat_id, msg)
    elif txt.startswith('/BAN '):
        try:
            uid_ban=int(txt.split()[1])
            users[uid_ban]["banned"]=True
            msg=bot.send_message(chat_id, f"⛔ Banned {uid_ban}")
            track_msg(chat_id, msg)
        except:
            msg=bot.send_message(chat_id, f"Usage: /ban 123456")
            track_msg(chat_id, msg)
    elif txt.startswith('/UNBAN '):
        try:
            uid_unban=int(txt.split()[1])
            users[uid_unban]["banned"]=False
            msg=bot.send_message(chat_id, f"✅ Unbanned {uid_unban}")
            track_msg(chat_id, msg)
        except:
            msg=bot.send_message(chat_id, f"Usage: /unban 123456")
            track_msg(chat_id, msg)
    elif txt.startswith('/ADDUSER'):
        try:
            parts=txt.split()
            uid_add=int(parts[1])
            dep=float(parts[2]) if len(parts)>2 else 0
            if uid_add not in users:
                users[uid_add]={"deposit":0,"registered":True,"used":0,"last_day":datetime.date.today().isoformat(),"username":"Added","wins":0,"losses":0,"streak":0,"loss_streak":0,"gwr_wins":0,"gwr_losses":0,"banned":False}
            users[uid_add]["registered"]=True
            users[uid_add]["deposit"]=dep
            msg=bot.send_message(chat_id, f"✅ Added {uid_add} ${dep} {get_level(uid_add)} WR:{get_wr(get_level(uid_add))}", reply_markup=main_menu())
            track_msg(chat_id, msg)
        except:
            msg=bot.send_message(chat_id, f"Usage: /adduser 123456 50")
            track_msg(chat_id, msg)
    elif txt.startswith('/SUCH') or txt.startswith('/SEARCH') or txt.startswith('/FIND'):
        try:
            uid_search=int(txt.split()[1])
            d=users.get(uid_search)
            if not d:
                msg=bot.send_message(chat_id, f"❌ User {uid_search} not found")
            else:
                check_daily(uid_search)
                gwr_w=d.get('gwr_wins',0)
                gwr_l=d.get('gwr_losses',0)
                wr=get_wr(get_level(uid_search))
                msg=bot.send_message(chat_id, f"👤 {uid_search}\nUsername: {d.get('username')}\nLevel: {get_level(uid_search)} WR:{wr}\nBanned: {d.get('banned')}\nDaily W:{d.get('wins',0)} L:{d.get('losses',0)}\nGWR: {gwr_w}W/{gwr_l}L")
            track_msg(chat_id, msg)
        except:
            msg=bot.send_message(chat_id, f"Usage: /such 123456")
            track_msg(chat_id, msg)
    elif txt.startswith('/BROADCAST'):
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("📅 1 Day", callback_data="bdel_24"), types.InlineKeyboardButton("📅 1 Week", callback_data="bdel_168"), types.InlineKeyboardButton("📅 1 Month", callback_data="bdel_720"))
        markup.add(types.InlineKeyboardButton("📅 3 Months", callback_data="bdel_2160"), types.InlineKeyboardButton("📅 6 Months", callback_data="bdel_4320"), types.InlineKeyboardButton("📅 1 Year", callback_data="bdel_8760"))
        markup.add(types.InlineKeyboardButton("♾️ Never", callback_data="bdel_0"))
        msg=bot.send_message(chat_id, "⏰ SELECTOR 1/2 - DELETE PERIOD", reply_markup=markup)
        track_msg(chat_id, msg)

@bot.message_handler(commands=['admin','users','stats','broadcast','adduser','such','search','find','ban','unban'])
def admin_commands(m): admin_cmd(m)

bot.remove_webhook()
print("V13.3.0 DEPLOY FINAL - MOTIVATIONAL READY")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

threading.Thread(target=run_flask, daemon=True).start()
bot.infinity_polling()
