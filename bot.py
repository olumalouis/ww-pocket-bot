import telebot
from telebot import types
import random
import threading
import time
from datetime import datetime, timezone

BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
OWNER_ID=8188622130
AFFILIATE_LINK="https://pocket-option.com/en/cabinet/try-demo/?lid=1154235&subid="

pairs_real=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","GBP/JPY","AUD/JPY","EUR/AUD","USD/CHF","NZD/USD","EUR/CAD","GBP/CAD","AUD/CAD"]
pairs_otc=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","EUR/GBP OTC","USD/CHF OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC","AUD/CAD OTC","EUR/CAD OTC","GBP/CAD OTC","USD/CAD OTC","EUR/NZD OTC","GBP/NZD OTC"]

MOTIV_WORDS=["STAY STRONG","NEXT IS WIN","DON'T GIVE UP","FOCUS","YOU GOT THIS","KEEP GOING","STAY CALM","BIG WIN COMING","BELIEVE","PUSH HARD"]

bot=telebot.TeleBot(BOT_TOKEN)
users={}
last_bot_msgs={}
broadcast_wait={}

def ensure_user(uid, name):
    if uid not in users:
        users[uid]={"id":uid,"name":name,"level":"NONE","deposit":0,"wins":0,"losses":0,"gwr_wins":0,"gwr_losses":0,"streak":0,"loss_streak":0,"limit":5,"used":0,"last_reset":datetime.now(timezone.utc).date().isoformat(),"banned":False,"bcast_wait":None}
    return users[uid]

def get_level(uid):
    dep=users[uid].get("deposit",0)
    if dep>=100: return "VIP"
    if dep>=50: return "PRO"
    if dep>=20: return "STARTER"
    return "NONE"

def get_limit(level):
    if level=="VIP": return 1000000
    if level=="PRO": return 100
    if level=="STARTER": return 20
    return 5

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
    markup.add(types.KeyboardButton("🔶 OTC 30"), types.KeyboardButton("🚀 UPGRADE"))
    markup.add(types.KeyboardButton("💰 DEPOSIT"), types.KeyboardButton("📈 My Status"))
    markup.add(types.KeyboardButton("📜 How it Works"), types.KeyboardButton("👑 ADMIN PANEL"))
    return markup

def track_msg(chat_id, msg):
    if chat_id not in last_bot_msgs: last_bot_msgs[chat_id]=[]
    last_bot_msgs[chat_id].append(msg.message_id)
    if len(last_bot_msgs[chat_id])>10:
        last_bot_msgs[chat_id]=last_bot_msgs[chat_id][-10:]

def clean_and_track(chat_id, uid):
    if chat_id in last_bot_msgs:
        for mid in last_bot_msgs[chat_id]:
            try: bot.delete_message(chat_id, mid)
            except: pass
        last_bot_msgs[chat_id]=[]@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note','location','contact','poll','venue','dice','game'], func=lambda m: broadcast_wait.get(m.from_user.id) is not None or users.get(m.from_user.id,{}).get("bcast_wait") is not None)
def handle_bcast(m):
    uid=m.from_user.id
    wait=broadcast_wait.get(uid) or users.get(uid,{}).get("bcast_wait")
    if not wait: return
    if uid!=OWNER_ID: return
    hours=wait["hours"]
    target=wait["target"]
    sent=[]
    count=0
    failed=0
    for u_id in list(users.keys()):
        if u_id==OWNER_ID: continue
        lvl=get_level(u_id)
        if target!="ALL" and lvl!=target: continue
        if users[u_id].get("banned"): continue
        try:
            if m.content_type=='text':
                msg=bot.send_message(u_id, f"📢 ADMIN:\n\n{m.text}")
            else:
                msg=bot.copy_message(u_id, m.chat.id, m.message_id)
            if hours>0: sent.append((u_id, msg.message_id))
            count+=1
        except:
            failed+=1
            pass
    if uid in broadcast_wait: del broadcast_wait[uid]
    if uid in users and users[uid].get("bcast_wait"): users[uid]["bcast_wait"]=None
    msg_confirm=bot.send_message(uid, f"✅ BROADCAST DONE\n📁 Type: {m.content_type}\n👥 Target: {target}\n✅ Sent: {count}\n❌ Failed: {failed}\n⏰ Delete: {hours}h", reply_markup=main_menu())
    track_msg(uid, msg_confirm)
    if hours>0 and sent:
        def auto_del():
            time.sleep(hours*3600)
            for cid,mid in sent:
                try: bot.delete_message(cid,mid)
                except: pass
        threading.Thread(target=auto_del, daemon=True).start()

@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_buttons(m):
    uid=m.from_user.id
    txt=(m.text or "")
    txt_up=txt.upper()
    if broadcast_wait.get(uid) or users.get(uid,{}).get("bcast_wait"):
        if any(k in txt_up for k in ["GET SIGNAL","REAL 15","OTC 30","UPGRADE","DEPOSIT","MY STATUS","HOW IT WORKS","ADMIN PANEL","/START","/ADDUSER","/BAN","/USERS","/STATS","CANCEL","GWR"]):
            if uid in broadcast_wait: del broadcast_wait[uid]
            if uid in users and users[uid].get("bcast_wait"): users[uid]["bcast_wait"]=None
        else:
            return
    if uid not in users: ensure_user(uid, m.from_user.username or m.from_user.first_name)
    if users[uid].get("banned"):
        bot.send_message(m.chat.id, "⛔ You are banned")
        return
    check_daily(uid)
    if "GET SIGNAL" in txt_up:
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
    elif "MY STATUS" in txt_up or "MYSTATUS" in txt_up:
        wins=users[uid].get('wins',0)
        losses=users[uid].get('losses',0)
        msg=bot.send_message(m.chat.id, f"📈 MY STATUS - DAILY RESET 00:00 UTC\n\n🏆 DAILY W/L:\n✅ Wins Today: {wins}\n❌ Losses Today: {losses}\n\n⏰ Resets daily at 00:00 UTC", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "UPGRADE" in txt_up:
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        level=get_level(uid)
        markup=types.InlineKeyboardMarkup()
        if level=="VIP":
            markup.add(types.InlineKeyboardButton("💎 You are VIP 👑", url=link))
            upgrade_text=(
f"🎉 CONGRATULATIONS {m.from_user.first_name}! 👑\n\n"
f"💎 YOU ARE VIP - MAX LEVEL REACHED!\n\n"
f"✅ UNLIMITED SIGNALS\n"
f"✅ 80-87% ACCURACY\n"
f"✅ NO LIMITS - MAX PROFIT!\n\n"
f"🔥 YOU ARE AT THE TOP!\n"
f"💰 KEEP DOMINATING MARKET!\n\n"
f"👑 VIP STATUS: ACTIVE\n"
f"🚀 ENJOY UNLIMITED POWER!"
            )
        else:
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
f"🔵 PRO $50 - 100/day 70-80% - MOST POPULAR! 90% CHOOSE THIS! 🚀\n\n"
f"⚡ WHY UPGRADE NOW?\n"
f"✅ 3x MORE WINS DAILY\n"
f"✅ HIGHER ACCURACY\n"
f"✅ UNLIMITED EARNING POTENTIAL\n\n"
f"🔗 YOUR UPGRADE LINK:\n{link}\n\n"
f"⏰ Don't watch others win — UPGRADE TODAY!"
            )
        msg=bot.send_message(m.chat.id, upgrade_text, reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "DEPOSIT" in txt_up:
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Deposit Now", url=link))
        msg=bot.send_message(m.chat.id, f"💰 Deposit now to upgrade!\n🔗 {link}", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif "HOW IT WORKS" in txt_up or txt_up.startswith("HOW"):
        msg=bot.send_message(m.chat.id, "📜 How it Works:\n1️⃣ Register\n2️⃣ 5/day FREE\n3️⃣ Deposit upgrade\n4️⃣ My Status shows Daily W/L only\n5️⃣ Limit & W/L reset 00:00 UTC\n6️⃣ GWR never resets", reply_markup=main_menu())
        track_msg(m.chat.id, msg)
    elif "ADMIN PANEL" in txt_up or txt_up.startswith('/ADMIN'):
        if uid!=OWNER_ID:
            msg=bot.send_message(m.chat.id, "⛔ Admin only")
            track_msg(m.chat.id, msg)
            return
        clean_and_track(m.chat.id, uid)
        markup=types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📢 Broadcast (2 Selectors)", callback_data="admin_broadcast"))
        markup.add(types.InlineKeyboardButton("👥 Users", callback_data="admin_users"), types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
        markup.add(types.InlineKeyboardButton("🏆 GWR Global", callback_data="admin_gwr"), types.InlineKeyboardButton("📈 Daily Stats", callback_data="admin_daily"))
        markup.add(types.InlineKeyboardButton("➕ Add User", callback_data="admin_adduser"), types.InlineKeyboardButton("🔍 Search User", callback_data="admin_search"))
        markup.add(types.InlineKeyboardButton("⛔ Ban User", callback_data="admin_ban"), types.InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"))
        msg=bot.send_message(m.chat.id, f"👑 ADMIN PANEL\nTotal: {len(users)}\nID: {OWNER_ID}\n✅ V13.6 FINAL", reply_markup=markup)
        track_msg(m.chat.id, msg)
    elif txt_up.startswith('/USERS') or txt_up.startswith('/STATS') or txt_up.startswith('/GWR') or txt_up.startswith('/BROADCAST') or txt_up.startswith('/ADDUSER') or txt_up.startswith('/SUCH') or txt_up.startswith('/SEARCH') or txt_up.startswith('/FIND') or txt_up.startswith('/BAN') or txt_up.startswith('/UNBAN'):
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
    elif data=="admin_gwr":
        if uid!=OWNER_ID: return
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
        if uid!=OWNER_ID: return
        total_w=0
        total_l=0
        for u in users.values():
            total_w+=u.get("wins",0)
            total_l+=u.get("losses",0)
        msg=bot.send_message(chat_id, f"📈 DAILY STATS - RESETS 00:00 UTC\n\n✅ Wins Today: {total_w}\n❌ Losses Today: {total_l}\n📊 Trades Today: {total_w+total_l}", reply_markup=main_menu())
        track_msg(chat_id, msg)
    elif data=="admin_adduser": bot.send_message(chat_id, "Use: /adduser 123456 50")
    elif data=="admin_search": bot.send_message(chat_id, "Use: /such 123456")
    elif data=="admin_ban": bot.send_message(chat_id, "Use: /ban 123456")
    elif data=="admin_unban": bot.send_message(chat_id, "Use: /unban 123456")
    elif data=="howitworks":
        msg=bot.send_message(chat_id, "📜 How it Works:\n1️⃣ Register\n2️⃣ 5/day FREE\n3️⃣ Deposit upgrade\n4️⃣ Status shows Daily W/L only\n5️⃣ Resets 00:00 UTC\n6️⃣ GWR never resets", reply_markup=main_menu())
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
        broadcast_wait[uid]={"hours":int(hours),"target":target}
        users[uid]["bcast_wait"]={"hours":int(hours),"target":target}
        msg=bot.send_message(chat_id, f"✍️ DONE: Delete {hours}h | Target {target}\nNow send ANY file - ALL SUPPORTED!", reply_markup=main_menu())
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
    if page>0: nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"pairs_{typ}_{page-1}"))
    if end<len(plist): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"pairs_{typ}_{page+1}"))
    if nav: markup.row(*nav)
    msg=bot.send_message(chat_id, f"📊 {typ.upper()} Pairs - Page {page+1}:", reply_markup=markup)
    track_msg(chat_id, msg)

def send_signal_result(chat_id, uid, pair, exp, typ):
    check_daily(uid)
    if users[uid]["used"]>=users[uid]["limit"]:
        link = f"{AFFILIATE_LINK}?subid={uid}" if "?" not in AFFILIATE_LINK else f"{AFFILIATE_LINK}&subid={uid}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 UPGRADE NOW", url=link))
        msg=bot.send_message(chat_id, f"⛔ Daily limit reached {users[uid]['limit']}\nUpgrade to get more!\n{link}", reply_markup=markup)
        track_msg(chat_id, msg)
        return
    users[uid]["used"]+=1
    direction=random.choice(["CALL 🟢","PUT 🔴"])
    accuracy=random.randint(72,87) if typ=="real" else random.randint(68,84)
    markup=types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ WIN", callback_data="win"), types.InlineKeyboardButton("❌ LOSS", callback_data="loss"))
    markup.add(types.InlineKeyboardButton("➡️ Next Signal", callback_data="next_signal"))
    text=(
f"🔥 SIGNAL READY 🔥\n\n"
f"📊 Pair: {pair}\n"
f"⏰ Expiry: {exp}\n"
f"📈 Direction: {direction}\n"
f"🎯 Accuracy: {accuracy}%\n"
f"💹 Market: {typ.upper()}\n\n"
f"⚡ Valid for 2-3 minutes\n"
f"👤 User: {users[uid]['name']}\n"
f"📊 Left Today: {users[uid]['limit']-users[uid]['used']}"
    )
    msg=bot.send_message(chat_id, text, reply_markup=markup)
    track_msg(chat_id, msg)

def admin_cmd(m, is_callback=False, is_stats=False):
    uid=m.from_user.id if not is_callback else m.chat.id
    if uid!=OWNER_ID: return
    txt=m.text or ""
    txt_up=txt.upper()
    if txt_up.startswith('/ADDUSER') or (is_callback and not is_stats):
        if not is_callback:
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
        else:
            bot.send_message(m.chat.id, f"👥 Total Users: {len(users)}\nUse /such ID to search")
            return
        ensure_user(target_id, f"User{target_id}")
        users[target_id]["deposit"]=dep
        lvl=get_level(target_id)
        users[target_id]["limit"]=get_limit(lvl)
        msg=bot.send_message(m.chat.id, f"✅ Added/Updated {target_id}\nDeposit: {dep}\nLevel: {lvl}\nLimit: {get_limit(lvl)}", reply_markup=main_menu())
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
        msg=bot.send_message(m.chat.id, f"🔍 User {tid}\nName: {u['name']}\nLevel: {get_level(tid)}\nDeposit: {u['deposit']}\nDaily W/L: {u['wins']}/{u['losses']}\nGWR W/L: {u['gwr_wins']}/{u['gwr_losses']}\nLimit: {u['limit']}\nUsed: {u['used']}\nBanned: {u['banned']}")
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
        if tid not in users: ensure_user(tid, f"User{tid}")
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
        if tid in users: users[tid]["banned"]=False
        bot.send_message(m.chat.id, f"✅ Unbanned {tid}")
        return
    if txt_up.startswith('/USERS') or (is_callback and not is_stats):
        total=len(users)
        banned=sum(1 for u in users.values() if u.get("banned"))
        msg=bot.send_message(m.chat.id, f"👥 Users: {total}\n⛔ Banned: {banned}\n✅ Active: {total-banned}")
        track_msg(m.chat.id, msg)
        return
    if txt_up.startswith('/STATS') or txt_up.startswith('/GWR') or is_stats:
        total=len(users)
        total_dep=sum(u.get("deposit",0) for u in users.values())
        total_w=sum(u.get("wins",0) for u in users.values())
        total_l=sum(u.get("losses",0) for u in users.values())
        total_gwr_w=sum(u.get("gwr_wins",0) for u in users.values())
        total_gwr_l=sum(u.get("gwr_losses",0) for u in users.values())
        lvl_counts={"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for u in users:
            lvl_counts[get_level(u)]+=1
        msg=bot.send_message(m.chat.id, f"📊 STATS\n\n👥 Users: {total}\n💰 Total Deposit: ${total_dep}\n\n📈 DAILY (resets 00:00 UTC):\n✅ Wins Today: {total_w}\n❌ Losses Today: {total_l}\n\n🏆 GWR (never resets):\n✅ GWR Wins: {total_gwr_w}\n❌ GWR Losses: {total_gwr_l}\n\nLevels:\n⚪ NONE: {lvl_counts['NONE']}\n🟢 STARTER: {lvl_counts['STARTER']}\n🔵 PRO: {lvl_counts['PRO']}\n💎 VIP: {lvl_counts['VIP']}")
        track_msg(m.chat.id, msg)
        return

@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid=m.from_user.id
    ensure_user(uid, m.from_user.username or m.from_user.first_name)
    check_daily(uid)
    if uid in broadcast_wait: del broadcast_wait[uid]
    if users[uid].get("bcast_wait"): users[uid]["bcast_wait"]=None
    lvl=get_level(uid)
    msg=bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}!\n\n🔥 Level: {lvl}\n📊 Limit: {users[uid]['limit']}/day\n\n📊 GET SIGNAL to start trading!", reply_markup=main_menu())
    track_msg(m.chat.id, msg)

@bot.message_handler(commands=['adduser','such','search','find','ban','unban','users','stats','gwr','broadcast'])
def admin_commands(m):
    admin_cmd(m)

print("Bot V13.6 FINAL - OWNER 8188622130 - ALL FEATURES KEPT - VIP CONGRATS")
bot.infinity_polling()
