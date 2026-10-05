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
last_bot_msgs = {}
pairs_real = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","EUR/JPY","USD/CHF","GBP/JPY","EUR/GBP","AUD/JPY","NZD/USD","EUR/AUD","GBP/AUD","USD/CAD","EUR/CAD","AUD/CAD"]
pairs_otc = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","USD/CHF OTC","GBP/JPY OTC","EUR/GBP OTC","AUD/JPY OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC","USD/CAD OTC","EUR/CAD OTC","AUD/CAD OTC","EUR/NZD OTC","GBP/NZD OTC","AUD/NZD OTC","EUR/CHF OTC","GBP/CHF OTC","AUD/CHF OTC","NZD/JPY OTC","CAD/JPY OTC","CHF/JPY OTC","EUR/JPY OTC","USD/BRL OTC","EUR/BRL OTC","GBP/BRL OTC","USD/INR OTC","EUR/INR OTC"]

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
        users[uid]={"deposit":0,"registered":False,"used":0,"last_day":datetime.date.today().isoformat(),"username":username,"wins":0,"losses":0,"streak":0,"loss_streak":0}
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
    markup.add(types.KeyboardButton("📈 My Status"), types.KeyboardButton("📜 How it Works"))
    markup.add(types.KeyboardButton("👑 Admin Panel"))
    return markup

@app.route('/')
def home(): return "V13.1.8 FINAL RUNNING"

@app.route('/postback')
def postback():
    tid=request.args.get('click_id') or request.args.get('subid')
    dep=request.args.get('sum_deposit') or 0
    try: dep=float(dep)
    except: dep=0
    if not tid: return "No ID",400
    try: tid=int(tid)
    except: return "Bad ID",400
    if tid not in users:
        users[tid]={"deposit":0,"registered":False,"used":0,"last_day":datetime.date.today().isoformat(),"username":"Unknown","wins":0,"losses":0,"streak":0,"loss_streak":0}
    users[tid]["registered"]=True
    if dep>0:
        users[tid]["deposit"]=max(users[tid].get("deposit",0), dep)
        try: bot.send_message(tid, f"💰 Deposit ${dep} confirmed! Level: {get_level(tid)}", reply_markup=main_menu())
        except: pass
    else:
        try: bot.send_message(tid, f"✅ Registration confirmed! 5/day unlocked", reply_markup=main_menu())
        except: pass
    return "OK",200

@bot.message_handler(commands=['start'])
def start(m):
    uid=m.from_user.id
    ensure_user(uid, m.from_user.username or m.from_user.first_name)
    check_daily(uid)
    level=get_level(uid)
    clean_and_track(m.chat.id, uid)
    if level=="LOCKED":
        link=f"{AFFILIATE_LINK}?subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Register Now - Unlock 5/day", url=link))
        msg=bot.send_message(m.chat.id, "🔒 LOCKED - REGISTER FIRST", reply_markup=markup)
        track_msg(m.chat.id, msg)
    else:
        used=users[uid].get("used",0)
        limit=get_limit(level)
        remains=limit-used if limit<999999 else 999
        wr=get_wr(level)
        msg=bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}!\n👑 {level} | 🎯 {wr} WR\n📊 {used}/{limit if limit<999999 else '∞'} Used | {remains if remains!=999 else '∞'} Remains", reply_markup=main_menu())
        track_msg(m.chat.id, msg)@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_buttons(m):
    if users.get(m.from_user.id,{}).get("bcast_wait"): return
    txt=m.text.strip()
    uid=m.from_user.id
    if uid not in users: ensure_user(uid, m.from_user.username or m.from_user.first_name)
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
        msg=bot.send_message(m.chat.id, f"👤 STATUS\n👑 {level}\n💰 ${users[uid].get('deposit',0)}\n📊 Today: {used}/{limit if limit<999999 else '∞'}\n🏆 W:{users[uid].get('wins',0)} L:{users[uid].get('losses',0)}", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "Upgrade" in txt:
        link=f"{AFFILIATE_LINK}?subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚪ NONE $0 5/day", url=link))
        markup.add(types.InlineKeyboardButton("🟢 STARTER $20 20/day", url=link))
        markup.add(types.InlineKeyboardButton("🔵 PRO $50 100/day POPULAR", url=link))
        markup.add(types.InlineKeyboardButton("💎 VIP $100 UNLIMITED BEST", url=link))
        msg=bot.send_message(m.chat.id, "💎 UPGRADE PLANS:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "Deposit" in txt:
        link=f"{AFFILIATE_LINK}?subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Deposit Now", url=link))
        msg=bot.send_message(m.chat.id, "💰 Deposit to upgrade:", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "How it Works" in txt:
        msg=bot.send_message(m.chat.id, "📜 How it Works:\n1️⃣ Register\n2️⃣ Get 5/day\n3️⃣ Deposit to upgrade\n4️⃣ GET SIGNAL\n5️⃣ WIN/LOSS daily reset", reply_markup=main_menu())
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
        msg=bot.send_message(m.chat.id, f"👑 ADMIN PANEL\nTotal: {len(users)}\n✅ 2 SELECTORS BROADCAST\n✅ Commands auto-delete only\n✅ Broadcast excluded", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif txt.startswith('/users') or txt.startswith('/stats') or txt.startswith('/broadcast') or txt.startswith('/adduser') or txt.startswith('/such') or txt.startswith('/search') or txt.startswith('/find'):
        admin_cmd(m)

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid=c.from_user.id
    data=c.data
    chat_id=c.message.chat.id
    ensure_user(uid, c.from_user.username or c.from_user.first_name)
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
        users[uid]["wins"]+=1
        users[uid]["streak"]+=1
        users[uid]["loss_streak"]=0
        msg=bot.send_message(chat_id, f"BOOM! WIN! 🔥 Streak: {users[uid]['streak']} W:{users[uid]['wins']} L:{users[uid]['losses']}", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="loss":
        users[uid]["losses"]+=1
        users[uid]["loss_streak"]+=1
        users[uid]["streak"]=0
        txt=f"☕ {users[uid]['loss_streak']} Losses — break!" if users[uid]['loss_streak']>=6 else f"Next WIN coming 💪 W:{users[uid]['wins']} L:{users[uid]['losses']}"
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="admin_users": admin_cmd(c.message, True)
    elif data=="admin_stats": admin_cmd(c.message, True, True)
    elif data=="admin_adduser": bot.send_message(chat_id, "Use: /adduser 123456 50")
    elif data=="admin_search": bot.send_message(chat_id, "Use: /such 123456")

    # ====== BROADCAST 2 SELECTORS ======
    elif data=="admin_broadcast":
        if uid!=OWNER_ID: return
        # SELECTOR 1 - AUTO DELETE PERIOD
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⏰ 1 Hour", callback_data="bdel_1"), types.InlineKeyboardButton("⏰ 6 Hours", callback_data="bdel_6"))
        markup.add(types.InlineKeyboardButton("⏰ 12 Hours", callback_data="bdel_12"), types.InlineKeyboardButton("⏰ 24 Hours", callback_data="bdel_24"))
        markup.add(types.InlineKeyboardButton("♾️ Never Delete", callback_data="bdel_0"))
        msg=bot.send_message(chat_id, "⏰ SELECTOR 1/2 - AUTO DELETE PERIOD:\nChoose how long broadcast stays (broadcast only, not commands)", reply_markup=markup)
        track_msg(chat_id, msg)

    elif data.startswith("bdel_"):
        if uid!=OWNER_ID: return
        hours=int(data.split("_")[1])
        # SELECTOR 2 - LEVEL TARGET
        markup=types.InlineKeyboardMarkup(row_width=3)
        markup.add(types.InlineKeyboardButton("ALL", callback_data=f"bcast_{hours}_ALL"), types.InlineKeyboardButton("NONE", callback_data=f"bcast_{hours}_NONE"), types.InlineKeyboardButton("STARTER", callback_data=f"bcast_{hours}_STARTER"))
        markup.add(types.InlineKeyboardButton("PRO", callback_data=f"bcast_{hours}_PRO"), types.InlineKeyboardButton("VIP", callback_data=f"bcast_{hours}_VIP"))
        msg=bot.send_message(chat_id, f"✅ Selector 1: Delete after {hours}h\n\n👥 SELECTOR 2/2 - SELECT TARGET LEVEL:\nNow choose who receives broadcast", reply_markup=markup)
        track_msg(chat_id, msg)

    elif data.startswith("bcast_"):
        if uid!=OWNER_ID: return
        _, hours, target = data.split("_")
        users[uid]["bcast_wait"]={"hours":int(hours),"target":target}
        msg=bot.send_message(chat_id, f"✍️ BOTH SELECTORS DONE:\n⏰ Delete: {hours}h | 👥 Target: {target}\n\nNow send ANY file type - text, photo, video, document, audio, voice, sticker\nBroadcast EXCLUDED from command auto-delete!")
        track_msg(chat_id, msg)

@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'], func=lambda m: users.get(m.from_user.id,{}).get("bcast_wait") is not None and m.from_user.id==OWNER_ID)
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
    msg_confirm=bot.send_message(uid, f"✅ 2 SELECTORS BROADCAST DONE\n📄 Type: {m.content_type}\n👥 Target: {target} = {count} users\n⏰ Auto delete: {hours}h (broadcast only)\n✅ Broadcast EXCLUDED from command cleaner", reply_markup=main_menu())
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
        if "/admin" in txt:
            msg=bot.send_message(chat_id, "⛔ Admin only")
            track_msg(chat_id, msg)
        return
    if is_callback:
        if is_stats:
            c={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
            for u in users: c[get_level(u)]+=1
            msg=bot.send_message(chat_id, f"📊 {c} FINAL ✅")
            track_msg(chat_id, msg)
        else:
            out="👥 USERS:\n"
            for uid_,d in list(users.items())[:40]:
                out+=f"{uid_} {d.get('username')} {get_level(uid_)} ${d.get('deposit',0)} W:{d.get('wins',0)} L:{d.get('losses',0)}\n"
            msg=bot.send_message(chat_id, out)
            track_msg(chat_id, msg)
        return
    if txt.startswith('/users'):
        out="👥 USERS:\n"
        for uid_,d in list(users.items())[:40]:
            out+=f"{uid_} {d.get('username')} {get_level(uid_)} ${d.get('deposit',0)} W:{d.get('wins',0)} L:{d.get('losses',0)}\n"
        msg=bot.send_message(chat_id, out)
        track_msg(chat_id, msg)
    elif txt.startswith('/stats'):
        c={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for u in users: c[get_level(u)]+=1
        msg=bot.send_message(chat_id, f"📊 {c} FINAL ✅")
        track_msg(chat_id, msg)
    elif txt.startswith('/adduser'):
        try:
            parts=txt.split()
            uid_add=int(parts[1])
            dep=float(parts[2]) if len(parts)>2 else 0
            if uid_add not in users:
                users[uid_add]={"deposit":0,"registered":True,"used":0,"last_day":datetime.date.today().isoformat(),"username":"Added","wins":0,"losses":0,"streak":0,"loss_streak":0}
            users[uid_add]["registered"]=True
            users[uid_add]["deposit"]=dep
            msg=bot.send_message(chat_id, f"✅ Added user {uid_add} deposit ${dep} Level {get_level(uid_add)}", reply_markup=main_menu())
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
                msg=bot.send_message(chat_id, f"👤 User {uid_search}\nUsername: {d.get('username')}\nLevel: {get_level(uid_search)}\nDeposit: ${d.get('deposit',0)}\nUsed: {d.get('used',0)}/{get_limit(get_level(uid_search))}\nW:{d.get('wins',0)} L:{d.get('losses',0)}")
            track_msg(chat_id, msg)
        except Exception as e:
            msg=bot.send_message(chat_id, f"Usage: /such 123456\nError {e}")
            track_msg(chat_id, msg)
    elif txt.startswith('/broadcast'):
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⏰ 1h", callback_data="bdel_1"), types.InlineKeyboardButton("⏰ 6h", callback_data="bdel_6"))
        markup.add(types.InlineKeyboardButton("⏰ 12h", callback_data="bdel_12"), types.InlineKeyboardButton("⏰ 24h", callback_data="bdel_24"))
        markup.add(types.InlineKeyboardButton("♾️ Never", callback_data="bdel_0"))
        msg=bot.send_message(chat_id, "⏰ SELECTOR 1/2 - AUTO DELETE PERIOD:", reply_markup=markup)
        track_msg(chat_id, msg)

@bot.message_handler(commands=['admin','users','stats','broadcast','adduser','such','search','find'])
def admin_commands(m): admin_cmd(m)

bot.remove_webhook()
print("V13.1.8 FINAL - 2 SELECTORS CONFIRMED")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

threading.Thread(target=run_flask, daemon=True).start()
bot.infinity_polling()
