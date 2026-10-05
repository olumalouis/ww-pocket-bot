import os, json, random, time, threading
from datetime import datetime, date, timedelta
from flask import Flask
import telebot
from telebot import types

TOKEN=os.getenv("TOKEN") or os.getenv("BOT_TOKEN") or "YOUR_TOKEN_HERE"
OWNER=str(os.getenv("OWNER_ID") or os.getenv("OWNER") or "7133772812")
LINK=os.getenv("LINK","https://yourlink.com")

bot=telebot.TeleBot(TOKEN, threaded=True)
app=Flask(__name__)

REAL=["EURUSD","GBPUSD","USDJPY","AUDUSD","EURGBP","USDCAD","GBPJPY","EURJPY"]
OTC=["EURUSD_OTC","GBPUSD_OTC","USDJPY_OTC","AUDUSD_OTC","EURGBP_OTC","GBPJPY_OTC","EURJPY_OTC","AUDJPY_OTC","NZDUSD_OTC","USDCAD_OTC","EURCHF_OTC","GBPCHF_OTC","CHFJPY_OTC","EURCAD_OTC","AUDCAD_OTC","CADJPY_OTC","GBPAUD_OTC","EURAUD_OTC","AUDCHF_OTC"]
EXP=["M1","M2","M3","M5"]

msg_hist={}; broadcast_data={}; add_pending={}

def load_db():
    try:
        if os.path.exists("db.json"):
            with open("db.json","r") as f: return json.load(f)
    except: pass
    return {}
def save(d):
    try:
        with open("db.json","w") as f: json.dump(d,f)
    except: pass
def load_admin():
    try:
        if os.path.exists("admin.json"):
            with open("admin.json","r") as f: return json.load(f)
    except: pass
    return {"total_wins":0,"total_losses":0}
def save_admin(d):
    try:
        with open("admin.json","w") as f: json.dump(d,f)
    except: pass
def load_broadcast():
    try:
        if os.path.exists("broadcast.json"):
            with open("broadcast.json","r") as f: return json.load(f)
    except: pass
    return []
def save_broadcast(d):
    try:
        with open("broadcast.json","w") as f: json.dump(d,f)
    except: pass

def ensure(uid):
    d=load_db()
    if uid not in d:
        d[uid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
        save(d)
    return d[uid]

def get_lvl(uid):
    d=load_db();u=d.get(uid)
    if not u: return "none"
    if u.get("expires_at") and u["expires_at"]!="lifetime":
        try:
            exp=datetime.fromisoformat(u["expires_at"])
            if datetime.now()>exp: u["level"]="none";u["verified"]=False;d[uid]=u;save(d);return "none"
        except: pass
    return u.get("level","none")

def check_limit(uid,lvl):
    d=load_db();u=d.get(uid,{});today=str(date.today())
    if u.get("date")!=today:
        u["today"]=0;u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0;u["today_wins"]=0;u["today_losses"]=0;u["date"]=today;d[uid]=u;save(d)
    cur=u.get("today",0)
    if lvl=="vip": return False,cur,9999
    if lvl=="starter": lim=20
    elif lvl=="pro": lim=50
    else: lim=3
    return cur>=lim,cur,lim

def inc(uid):
    d=load_db();u=d.get(uid)
    if u:
        if u.get("date")!=str(date.today()): u["today"]=0;u["date"]=str(date.today())
        u["today"]=u.get("today",0)+1;d[uid]=u;save(d)

def get_sig(pair,exp,lvl):
    conf=random.randint(85,96) if lvl in ["vip","pro"] else random.randint(72,88)
    sig="BUY" if random.random()>0.5 else "SELL"
    rsi=random.uniform(25,75);trend="Up" if "BUY" in sig else "Down"
    return sig,rsi,trend,conf

def store_and_cleanup(chat_id, msg_id):
    if chat_id not in msg_hist: msg_hist[chat_id]=[]
    msg_hist[chat_id].append(msg_id)
    def do_cleanup():
        time.sleep(1.2)
        if chat_id in msg_hist and len(msg_hist[chat_id])>1:
            for old_id in msg_hist[chat_id][:-1]:
                try: bot.delete_message(chat_id, old_id)
                except: pass
            msg_hist[chat_id]=msg_hist[chat_id][-1:]
    threading.Thread(target=do_cleanup, daemon=True).start()

def get_main_kb(uid):
    k=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    k.add(types.KeyboardButton("🚀 Get Signal 🔥"))
    k.add(types.KeyboardButton("💰 Deposit"), types.KeyboardButton("❓ How"))
    k.add(types.KeyboardButton("👤 Status"), types.KeyboardButton("📞 Support"))
    k.add(types.KeyboardButton("🚀 Upgrade"))
    if str(uid)==OWNER: k.add(types.KeyboardButton("👑 Admin"))
    return k

def signal_keyboard():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
    k.add(types.InlineKeyboardButton("🔥 Next Signal",callback_data="sel_market"))
    return k

@app.route('/')
def home(): return "Bot Running V11.1 Fixed 🔥"

@bot.message_handler(commands=["start","clearme","cancel"])
def start_cmd(m):
    chat_id=m.chat.id;uid=str(m.from_user.id)
    # FIX: clear stuck broadcast state
    if uid==OWNER and m.text.startswith("/cancel"):
        broadcast_data.pop(uid,None); add_pending.pop(uid,None)
        bot.send_message(chat_id,"✅ Cancelled broadcast/add - Now try /start"); return
    if m.text.startswith("/clearme") and uid!=OWNER: return
    if m.text.startswith("/clearme"):
        if chat_id in msg_hist:
            for mid in msg_hist[chat_id]:
                try: bot.delete_message(chat_id, mid)
                except: pass
            msg_hist[chat_id]=[]
        bot.send_message(chat_id,"✅ Cleared! /start"); return
    u=ensure(uid);lvl=get_lvl(uid);name=m.from_user.first_name or "Trader"
    txt=f"👋 Welcome {name}!\n👑 {lvl.upper()} 📊 Today {u.get('today',0)} | {u.get('today_wins',0)}W-{u.get('today_losses',0)}L\n🔥 Ready?"
    mm=bot.send_message(chat_id, txt, reply_markup=get_main_kb(uid))
    store_and_cleanup(chat_id, mm.message_id)@bot.message_handler(content_types=['text','photo','video','document','animation'], func=lambda m: str(m.from_user.id)==OWNER and (str(m.from_user.id) in broadcast_data or str(m.from_user.id) in add_pending) and not (m.text and m.text.startswith("/")))
def owner_pending_handler(m):
    tid=str(m.from_user.id); chat_id=m.chat.id
    if tid in add_pending:
        try:
            level=add_pending.get(tid);txt=m.text or "";uid_input=txt.strip().replace("@","").split()[0] if txt else ""
            if not uid_input.isdigit():
                mm=bot.send_message(chat_id,"❌ Send NUMERIC ID only! Ex: 7123456789\n/cancel to exit"); store_and_cleanup(chat_id, mm.message_id); return
            uid=uid_input;d=load_db();mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
            lvl_clean=level.lower().split("_")[0]
            if lvl_clean not in mp:
                mm=bot.send_message(chat_id,"❌ Invalid level"); store_and_cleanup(chat_id, mm.message_id); add_pending.pop(tid,None); return
            total_val=mp[lvl_clean];final_level="none" if lvl_clean=="free" else ("vip" if lvl_clean=="lifetime" else lvl_clean);verified=lvl_clean!="free"
            d[uid]={"total":total_val,"level":final_level,"verified":verified,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
            if lvl_clean=="free": d[uid]["level"]="none"
            if lvl_clean=="lifetime": d[uid]["expires_at"]="lifetime"
            save(d);add_pending.pop(tid,None)
            mm=bot.send_message(chat_id,f"✅ Added {uid} as {lvl_clean.upper()} 👑"); store_and_cleanup(chat_id, mm.message_id)
        except Exception as e:
            add_pending.pop(tid,None)
            mm=bot.send_message(chat_id,f"❌ Error: {e}"); store_and_cleanup(chat_id, mm.message_id)
        return
    if tid in broadcast_data:
        target=broadcast_data.get(tid)
        tval=target["target"] if isinstance(target, dict) else target if isinstance(target,str) else "ALL"
        if isinstance(target, dict) and target.get("type")!="pending": data=target
        else: data={"target": tval}
        if m.content_type=="photo": data["type"]="photo";data["file_id"]=m.photo[-1].file_id;data["caption"]=m.caption or ""
        elif m.content_type=="video": data["type"]="video";data["file_id"]=m.video.file_id;data["caption"]=m.caption or ""
        elif m.content_type=="document": data["type"]="document";data["file_id"]=m.document.file_id;data["caption"]=m.caption or ""
        elif m.content_type=="animation": data["type"]="animation";data["file_id"]=m.animation.file_id;data["caption"]=m.caption or ""
        else: data["type"]="text";data["text"]=m.text or "";data["caption"]=m.text or ""
        data["target"]=tval
        broadcast_data[tid]=data
        k=types.InlineKeyboardMarkup(row_width=2)
        k.add(types.InlineKeyboardButton("♾️ No Delete",callback_data="del_none"))
        k.add(types.InlineKeyboardButton("🗓️ 1 Week",callback_data="del_7"),types.InlineKeyboardButton("📅 1 Month",callback_data="del_30"))
        k.add(types.InlineKeyboardButton("📆 3 Months",callback_data="del_90"),types.InlineKeyboardButton("🗓️ 6 Months",callback_data="del_180"))
        k.add(types.InlineKeyboardButton("📅 1 Year",callback_data="del_365"))
        mm=bot.send_message(chat_id,f"✅ Saved Type:{data['type']} Target:{data['target']}\n\n⏰ When to delete BROADCAST from users?",reply_markup=k)
        store_and_cleanup(chat_id, mm.message_id); return

@bot.message_handler(commands=["adduser","broadcast","ban","unban"])
def admin_cmds(m):
    if str(m.from_user.id)!=OWNER: return
    chat_id=m.chat.id; a=m.text.split()
    cmd=a[0].replace("/","").split("@")[0] if a else ""
    if cmd=="adduser":
        if len(a)<3:
            mm=bot.send_message(chat_id,"❌ /adduser ID LEVEL\nEx: /adduser 123456 VIP"); store_and_cleanup(chat_id, mm.message_id); return
        uid=a[1].strip().replace("@","");lvl=a[2].lower().strip();days=None
        if len(a)>=4:
            try: days=int(a[3])
            except: days=None
        mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
        if lvl not in mp:
            mm=bot.send_message(chat_id,f"❌ Invalid {lvl}"); store_and_cleanup(chat_id, mm.message_id); return
        d=load_db();final_level="none" if lvl=="free" else ("vip" if lvl=="lifetime" else lvl);verified=lvl!="free"
        d[uid]={"total":mp[lvl],"level":final_level,"verified":verified,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
        if lvl=="free": d[uid]["level"]="none"
        if days: d[uid]["expires_at"]=(datetime.now()+timedelta(days=days)).isoformat()
        elif lvl=="lifetime": d[uid]["expires_at"]="lifetime"
        save(d)
        mm=bot.send_message(chat_id,f"✅ Added {uid} as {lvl.upper()} 👑"); store_and_cleanup(chat_id, mm.message_id); return

@bot.message_handler(func=lambda m: True)
def text_handler(m):
    chat_id=m.chat.id;uid=str(m.from_user.id);txt=(m.text or "").strip()
    if not txt: return
    if txt.startswith("/"): return
    # FIX: always ensure user exists - this was causing not replying
    ensure(uid)
    lvl=get_lvl(uid)
    if txt in ["🚀 Get Signal 🔥","Get Signal","/getsignal","Get Signal 🔥"]:
        k=types.InlineKeyboardMarkup(row_width=2)
        k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
        mm=bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k)
        store_and_cleanup(chat_id, mm.message_id); return
    if txt in ["💰 Deposit","Deposit"]:
        k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("💰 Deposit",url=LINK+"?click_id="+uid))
        mm=bot.send_message(chat_id,f"💰 DEPOSIT {LINK}?click_id={uid}",reply_markup=k)
        store_and_cleanup(chat_id, mm.message_id);return
    if txt in ["❓ How","How"]:
        mm=bot.send_message(chat_id,"❓ HOW: Register Deposit /start Get Signal")
        store_and_cleanup(chat_id, mm.message_id);return
    if txt in ["👤 Status","Status"]:
        u=ensure(uid);lim_txt="♾️" if lvl=="vip" else "20" if lvl=="starter" else "100" if lvl=="pro" else "3"
        mm=bot.send_message(chat_id,f"👤 Level:{lvl.upper()} Deposit:${u.get('total',0)} Today:{u.get('today',0)}/{lim_txt} | {u.get('today_wins',0)}W-{u.get('today_losses',0)}L")
        store_and_cleanup(chat_id, mm.message_id);return
    if txt in ["📞 Support","Support"]:
        mm=bot.send_message(chat_id,"📞 Support @YourSupport"); store_and_cleanup(chat_id, mm.message_id);return
    if txt in ["🚀 Upgrade","Upgrade"]:
        u=ensure(uid)
        k=types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("⭐ STARTER $20",url=LINK+"?click_id="+uid))
        k.add(types.InlineKeyboardButton("💎 PRO $50",url=LINK+"?click_id="+uid))
        k.add(types.InlineKeyboardButton("👑 VIP $100",url=LINK+"?click_id="+uid))
        mm=bot.send_message(chat_id,f"🚀 UPGRADE Level:{lvl.upper()} Deposit:${u.get('total',0)}",reply_markup=k)
        store_and_cleanup(chat_id, mm.message_id);return
    if txt in ["👑 Admin","Admin"] and uid==OWNER:
        k=types.InlineKeyboardMarkup(row_width=2)
        k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
        k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
        k.add(types.InlineKeyboardButton("➕ Add User 👑",callback_data="ad_adduser"))
        k.add(types.InlineKeyboardButton("💰 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
        k.add(types.InlineKeyboardButton("🔒 Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🏆 WR",callback_data="ad_wr"))
        mm=bot.send_message(chat_id,f"👑 ADMIN V11.1 👑\n👥 Users {len(load_db())}",reply_markup=k)
        store_and_cleanup(chat_id, mm.message_id); return
        @bot.callback_query_handler(func=lambda c: True)
def cb(c):
    try:
        bot.answer_callback_query(c.id)
        tid=str(c.from_user.id);data=c.data;chat_id=c.message.chat.id
        ensure(tid)
        lvl=get_lvl(tid)
        if data in ["res_win","res_loss"]:
            dbb=load_db();ud=dbb.get(tid);adm=load_admin()
            if not ud: ud=ensure(tid)
            if data=="res_win":
                ud["wins"]=ud.get("wins",0)+1;ud["today_wins"]=ud.get("today_wins",0)+1;ud["win_streak"]=ud.get("win_streak",0)+1;ud["loss_streak"]=0;dbb[tid]=ud;save(dbb)
                adm["total_wins"]=adm.get("total_wins",0)+1;save_admin(adm)
                win_list=[
                    f"✅ BOOM! WIN! 🔥💰\n🏆 Streak: {ud['win_streak']} Wins!\n🚀 Keep pushing {lvl.upper()}!",
                    f"✅ PERFECT WIN! 💎🔥\n📈 {ud['win_streak']} in a row! You're on fire!",
                    f"✅ KAZI WIN! 👑💸\n🔥 Win streak {ud['win_streak']} - Machine!",
                    f"✅ BANG! WIN CONFIRMED! 🚀\n💰 {ud['win_streak']} Wins straight! Keep going!"
                ]
                mm=bot.send_message(chat_id, random.choice(win_list), reply_markup=signal_keyboard())
                store_and_cleanup(chat_id, mm.message_id); return
            else:
                ud["losses"]=ud.get("losses",0)+1;ud["today_losses"]=ud.get("today_losses",0)+1;ud["loss_streak"]=ud.get("loss_streak",0)+1;ud["win_streak"]=0;dbb[tid]=ud;save(dbb)
                adm["total_losses"]=adm.get("total_losses",0)+1;save_admin(adm)
                ls=ud.get("loss_streak",1)
                if ls<=2:
                    loss_list=[
                        f"❌ Loss, but we learn! 📚\n💪 Loss streak {ls} - Next is WIN for sure!",
                        f"❌ Not today, but we fight! ⚔️\n🔥 {ls} loss - Market trick, we adapt!",
                        f"❌ Small loss! 💸\n🚀 Top traders lose too, WIN coming!"
                    ]
                    msg=random.choice(loss_list)
                elif ls==3:
                    msg=f"❌ 3 Losses in row 😤\n🧠 Don't revenge trade! Take small break\n💪 Next is WIN, trust KAZI!"
                elif ls==4:
                    msg=f"❌ 4 Losses 💔\n⚠️ Slow down boss! Reduce lot size\n🔥 We recover together!"
                elif ls==5:
                    msg=f"❌ 5 Losses in row! 🚨\n🛑 Almost at limit! 1 more = STOP\n🧘 Breathe, next will recover!"
                else:
                    msg=f"⚠️ WARNING! 6 LOSS STREAK 🚫\n\n🧠 Boss, STOP trading now!\n📉 Market is bad today, take a break!\n☕️ Rest 1 hour, clear mind!\n🔄 Come back fresh = WIN again!\n\n💡 Pro traders know when to STOP!\n🛑 Paused for your safety!\n\nStreak: {ls}L"
                    try: bot.send_message(chat_id, "🚨 STOP TRADING NOW 🚨\n"+msg)
                    except: pass
                mm=bot.send_message(chat_id, msg, reply_markup=signal_keyboard())
                store_and_cleanup(chat_id, mm.message_id); return
        if data=="admin" and tid==OWNER:
            k=types.InlineKeyboardMarkup(row_width=2)
            k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
            k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
            k.add(types.InlineKeyboardButton("➕ Add User 👑",callback_data="ad_adduser"))
            k.add(types.InlineKeyboardButton("💰 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
            k.add(types.InlineKeyboardButton("🔒 Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🏆 WR",callback_data="ad_wr"))
            mm=bot.send_message(chat_id,f"👑 ADMIN V11.1 👑\n👥 Users {len(load_db())}",reply_markup=k)
            store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and data.startswith("ad_"):
            if data=="ad_users":
                txt="👥 Users:\n"
                for uid,u in list(load_db().items())[:20]: txt+=f"{uid} {u.get('level')} ${u.get('total')} {u.get('today_wins',0)}W-{u.get('today_losses',0)}L\n"
                mm=bot.send_message(chat_id,txt); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_adduser":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="addlvl_free"))
                kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="addlvl_starter"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="addlvl_pro"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="addlvl_vip"))
                kb.add(types.InlineKeyboardButton("💎 LIFETIME ♾️",callback_data="addlvl_lifetime"))
                mm=bot.send_message(chat_id,"➕ SELECT LEVEL:",reply_markup=kb); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_stats":
                dd=load_db();tot=sum(u.get('total',0) for u in dd.values());ver=sum(1 for u in dd.values() if u.get('verified'))
                mm=bot.send_message(chat_id,f"📊 U:{len(dd)} V:{ver} ${tot}"); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_wr":
                adm=load_admin();wins=adm.get('total_wins',0);losses=adm.get('total_losses',0);total=wins+losses;wr=round(wins/total*100,1) if total>0 else 0
                mm=bot.send_message(chat_id,f"🏆 WR ✅ {wins} ❌ {losses} {wr}%"); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_deps":
                dd=load_db();txt="💰 Deposits:\n"
                for uid,u in dd.items():
                    if u.get('total',0)>0: txt+=f"{uid} ${u.get('total')}\n"
                mm=bot.send_message(chat_id,txt or "None"); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_reset":
                dd=load_db()
                for u in dd.values(): u["today"]=0;u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0;u["today_wins"]=0;u["today_losses"]=0;u["date"]=str(date.today())
                save(dd);mm=bot.send_message(chat_id,"🔄 Reset Done!"); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_broad":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL"))
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="broad_FREE"))
                kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="broad_STARTER"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="broad_PRO"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="broad_VIP"))
                kb.add(types.InlineKeyboardButton("💰 ALL VIPs",callback_data="broad_ALLVIP"))
                mm=bot.send_message(chat_id,"🎯 Select target:",reply_markup=kb); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_ban": mm=bot.send_message(chat_id,"🚫 /ban ID /unban ID"); store_and_cleanup(chat_id, mm.message_id); return
            if data=="ad_sec": mm=bot.send_message(chat_id,"🔒 Log empty"); store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and data.startswith("addlvl_"):
            level=data.replace("addlvl_","");add_pending[tid]=level
            mm=bot.send_message(chat_id,f"✅ Level {level.upper()} selected!\nSEND User ID:\n/cancel to exit"); store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and data.startswith("broad_"):
            target=data.replace("broad_","");broadcast_data[tid]={"target": target, "type": "pending"}
            mm=bot.send_message(chat_id,f"🎯 Target {target} ✅\nSEND broadcast msg:\n/cancel to exit"); store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and data.startswith("del_"):
            content=broadcast_data.get(tid)
            if not content or content.get("type")=="pending":
                mm=bot.send_message(chat_id,"❌ No broadcast content"); store_and_cleanup(chat_id, mm.message_id); return
            target=content["target"];days_str=data.replace("del_","");delete_days=None
            if days_str!="none":
                try: delete_days=int(days_str)
                except: delete_days=None
            cnt=0;dbs=load_db();b_list=load_broadcast();delete_at=None
            if delete_days: delete_at=datetime.now()+timedelta(days=delete_days)
            for uid,u in list(dbs.items()):
                lvl_u=u.get("level","none");ver=u.get("verified",False);send=False
                if target=="ALL": send=True
                elif target=="FREE" and not ver: send=True
                elif target=="STARTER" and lvl_u=="starter": send=True
                elif target=="PRO" and lvl_u=="pro": send=True
                elif target=="VIP" and lvl_u=="vip": send=True
                elif target=="ALLVIP" and lvl_u in ["starter","pro","vip"]: send=True
                if send:
                    try:
                        ctype=content.get("type","text")
                        if ctype=="photo": sent=bot.send_photo(uid, content["file_id"], caption=content.get("caption",""))
                        elif ctype=="video": sent=bot.send_video(uid, content["file_id"], caption=content.get("caption",""))
                        elif ctype=="document": sent=bot.send_document(uid, content["file_id"], caption=content.get("caption",""))
                        elif ctype=="animation": sent=bot.send_animation(uid, content["file_id"], caption=content.get("caption",""))
                        else:
                            txt=content.get("text","")
                            if not txt: continue
                            sent=bot.send_message(uid, txt)
                        cnt+=1
                        if delete_at: b_list.append({"chat_id": int(uid) if str(uid).isdigit() else uid, "msg_id": sent.message_id, "delete_at": delete_at.isoformat()})
                        time.sleep(0.05)
                    except: continue
            if delete_at:
                save_broadcast(b_list)
                mm=bot.send_message(chat_id,f"✅ Broadcast {cnt} users 🎯 {target}\n⏰ Delete in {delete_days} days");
            else:
                mm=bot.send_message(chat_id,f"✅ Broadcast {cnt} users 🎯 {target}\n♾️ No auto-delete");
            store_and_cleanup(chat_id, mm.message_id)
            if tid in broadcast_data: del broadcast_data[tid]
            return
        if data=="sel_market":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
            mm=bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if data=="m_real":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
            mm=bot.send_message(chat_id,"💹 REAL 15",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if data=="m_otc":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
            mm=bot.send_message(chat_id,"📊 OTC 30",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if data=="real_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in REAL: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_REAL"))
            mm=bot.send_message(chat_id,"✋ Pick Pair",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if data=="otc_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[:15]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("➡️ Next 15",callback_data="otc_manual2"))
            mm=bot.send_message(chat_id,"✋ OTC 1/2",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if data=="otc_manual2":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[15:]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("⬅️ Back",callback_data="otc_manual"))
            mm=bot.send_message(chat_id,"✋ OTC 2/2",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if data.startswith("pair_"):
            rest=data[5:];pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}"); store_and_cleanup(chat_id, mm.message_id);return
            k=types.InlineKeyboardMarkup(row_width=4)
            k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5"))
            mm=bot.send_message(chat_id,f"💹 {pair} Pick Expiry:",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if data in ["real_auto","otc_auto"]:
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}"); store_and_cleanup(chat_id, mm.message_id);return
            pairs=OTC if data.startswith("otc_") else REAL
            pair=random.choice(pairs);exp=random.choice(EXP)
            sig,rsi,trend,conf=get_sig(pair, exp, lvl);inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% 💹 {pair} {'📈 BUY' if 'BUY' in sig else '📉 SELL'} {sig} Exp {exp} RSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard())
            store_and_cleanup(chat_id, mm.message_id);return
        if data.startswith("sig_"):
            tmp=data[4:];idx=tmp.rfind("_M");pair=tmp[:idx];exp=tmp[idx+1:]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}"); store_and_cleanup(chat_id, mm.message_id);return
            sig,rsi,trend,conf=get_sig(pair, exp, lvl);inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% {pair} {'📈 BUY' if 'BUY' in sig else '📉 SELL'} {sig} Exp {exp} RSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard())
            store_and_cleanup(chat_id, mm.message_id);return
    except Exception as e: print(f"CB ERR {e}")

def auto_delete_worker():
    while True:
        try:
            bl=load_broadcast();now=datetime.now();new=[]
            for it in bl:
                try:
                    da=datetime.fromisoformat(it["delete_at"])
                    if now>=da:
                        try: bot.delete_message(it["chat_id"], it["msg_id"])
                        except: pass
                    else: new.append(it)
                except: continue
            if len(new)!=len(bl): save_broadcast(new)
        except: pass
        time.sleep(60)

def run_bot():
    try: bot.remove_webhook()
    except: pass
    time.sleep(1)
    bot.infinity_polling(skip_pending=True, timeout=20)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=auto_delete_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
