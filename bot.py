import os, json, random, time, threading
from datetime import datetime, date, timedelta
from flask import Flask
import telebot
from telebot import types

TOKEN=os.getenv("TOKEN","YOUR_TOKEN")
OWNER=str(os.getenv("OWNER_ID","7133772812"))
LINK=os.getenv("LINK","https://yourlink.com")
DB_FILE="db.json"
ADMIN_FILE="admin.json"
BROAD_FILE="broadcast.json"

bot=telebot.TeleBot(TOKEN, threaded=True)
app=Flask(__name__)

REAL=["EURUSD","GBPUSD","USDJPY","AUDUSD","EURGBP","USDCAD","GBPJPY","EURJPY"]
OTC=["EURUSD_OTC","GBPUSD_OTC","USDJPY_OTC","AUDUSD_OTC","EURGBP_OTC","GBPJPY_OTC","EURJPY_OTC","AUDJPY_OTC","NZDUSD_OTC","USDCAD_OTC","EURCHF_OTC","GBPCHF_OTC","CHFJPY_OTC","EURCAD_OTC","AUDCAD_OTC","CADJPY_OTC","GBPAUD_OTC","EURAUD_OTC","AUDCHF_OTC","GBP CAD_OTC"]
EXP=["M1","M2","M3","M5"]

msg_hist={}; broadcast_data={}; add_pending={}

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE,"r") as f: return json.load(f)
    except: pass
    return {}
def save(d):
    try:
        with open(DB_FILE,"w") as f: json.dump(d,f)
    except: pass
def load_admin():
    try:
        if os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE,"r") as f: return json.load(f)
    except: pass
    return {"total_wins":0,"total_losses":0}
def save_admin(d):
    try:
        with open(ADMIN_FILE,"w") as f: json.dump(d,f)
    except: pass
def load_broadcast():
    try:
        if os.path.exists(BROAD_FILE):
            with open(BROAD_FILE,"r") as f: return json.load(f)
    except: pass
    return []
def save_broadcast(d):
    try:
        with open(BROAD_FILE,"w") as f: json.dump(d,f)
    except: pass

def ensure(uid):
    d=load_db()
    if uid not in d:
        d[uid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
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
    if u.get("date")!=today: u["today"]=0;u["date"]=today;d[uid]=u;save(d)
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
    sig="📈 BUY" if random.random()>0.5 else "📉 SELL"
    rsi=random.uniform(25,75);trend="🔼 Up" if "BUY" in sig else "🔽 Down"
    return sig,rsi,trend,conf

def store_and_cleanup(chat_id, msg_id):
    if chat_id not in msg_hist: msg_hist[chat_id]=[]
    msg_hist[chat_id].append(msg_id)
    if len(msg_hist[chat_id])>30:
        old=msg_hist[chat_id].pop(0)
        try: bot.delete_message(chat_id, old)
        except: pass

def cleanup_old_messages(chat_id, new_msg_id):
    time.sleep(1)
    if chat_id not in msg_hist: return
    for mid in list(msg_hist[chat_id][:-1]):
        try: bot.delete_message(chat_id, mid)
        except: pass
    msg_hist[chat_id]=[new_msg_id] if new_msg_id else []

def get_main_kb(uid):
    lvl=get_lvl(uid)
    k=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    k.add(types.KeyboardButton("🚀 Get Signal 🔥"))
    k.add(types.KeyboardButton("💰 Deposit"), types.KeyboardButton("❓ How"))
    k.add(types.KeyboardButton("👤 Status"), types.KeyboardButton("📞 Support"))
    k.add(types.KeyboardButton("🚀 Upgrade"))
    if uid==OWNER: k.add(types.KeyboardButton("👑 Admin"))
    return k

def signal_keyboard():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
    k.add(types.InlineKeyboardButton("🔥 Next Signal",callback_data="sel_market"))
    return k

@app.route('/')
def home(): return "Bot Running V11"

@bot.message_handler(commands=["start","clearme"])
def start_cmd(m):
    chat_id=m.chat.id;uid=str(m.from_user.id)
    if m.text.startswith("/clearme") and uid!=OWNER: return
    if m.text.startswith("/clearme"):
        msg_hist[chat_id]=[];mm=bot.send_message(chat_id,"✅ Cleared! /start")
        store_and_cleanup(chat_id, mm.message_id)
        threading.Thread(target=cleanup_old_messages, args=(chat_id, mm.message_id), daemon=True).start()
        return
    u=ensure(uid);lvl=get_lvl(uid)
    name=m.from_user.first_name or "Trader"
    txt=f"👋 Welcome {name}!\n👑 {lvl.upper()} 📊 Today {u.get('today',0)}\n🔥 Ready?"
    mm=bot.send_message(chat_id, txt, reply_markup=get_main_kb(uid))
    store_and_cleanup(chat_id, mm.message_id)
    threading.Thread(target=cleanup_old_messages, args=(chat_id, mm.message_id), daemon=True).start()

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/") and str(m.from_user.id) not in broadcast_data and str(m.from_user.id) not in add_pending)
def text_handler(m):
    chat_id=m.chat.id;uid=str(m.from_user.id);txt=m.text.strip();lvl=get_lvl(uid)
    if txt in ["🚀 Get Signal 🔥","Get Signal"]:
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
        mm=bot.send_message(chat_id,f"👤 Level:{lvl.upper()} Deposit:${u.get('total',0)} Today:{u.get('today',0)}/{lim_txt}")
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
        mm=bot.send_message(chat_id,f"👑 ADMIN V11 👑\n👥 Users {len(load_db())}",reply_markup=k)
        store_and_cleanup(chat_id, mm.message_id); return@bot.message_handler(content_types=['text','photo','video','document','animation'], func=lambda m: str(m.from_user.id)==OWNER and (str(m.from_user.id) in broadcast_data or str(m.from_user.id) in add_pending) and not (m.text and m.text.startswith("/")))
def owner_pending_handler(m):
    tid=str(m.from_user.id); chat_id=m.chat.id
    if tid in add_pending:
        try:
            level=add_pending.get(tid);txt=m.text or "";uid_input=txt.strip().replace("@","").split()[0] if txt else ""
            if not uid_input.isdigit():
                mm=bot.send_message(chat_id,"❌ Send NUMERIC ID only! Ex: 7123456789")
                store_and_cleanup(chat_id, mm.message_id); return
            uid=uid_input;d=load_db();mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
            lvl_clean=level.lower().split("_")[0]
            if lvl_clean not in mp:
                mm=bot.send_message(chat_id,"❌ Invalid level"); store_and_cleanup(chat_id, mm.message_id); del add_pending[tid]; return
            total_val=mp[lvl_clean];final_level="none" if lvl_clean=="free" else ("vip" if lvl_clean=="lifetime" else lvl_clean);verified=lvl_clean!="free"
            d[uid]={"total":total_val,"level":final_level,"verified":verified,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
            if lvl_clean=="free": d[uid]["level"]="none"
            if lvl_clean=="lifetime": d[uid]["expires_at"]="lifetime"
            save(d);del add_pending[tid]
            mm=bot.send_message(chat_id,f"✅ Added {uid} as {lvl_clean.upper()} 👑")
            store_and_cleanup(chat_id, mm.message_id)
        except Exception as e:
            mm=bot.send_message(chat_id,f"❌ Error: {e}"); store_and_cleanup(chat_id, mm.message_id)
        return
    if tid in broadcast_data:
        target=broadcast_data.get(tid)
        if isinstance(target, dict) and target.get("type")!="pending":
            data=target
        else:
            tval=target["target"] if isinstance(target, dict) else target
            data={"target": tval}
        if m.content_type=="photo": data["type"]="photo";data["file_id"]=m.photo[-1].file_id;data["caption"]=m.caption or ""
        elif m.content_type=="video": data["type"]="video";data["file_id"]=m.video.file_id;data["caption"]=m.caption or ""
        elif m.content_type=="document": data["type"]="document";data["file_id"]=m.document.file_id;data["caption"]=m.caption or ""
        elif m.content_type=="animation": data["type"]="animation";data["file_id"]=m.animation.file_id;data["caption"]=m.caption or ""
        else: data["type"]="text";data["text"]=m.text or "";data["caption"]=m.text or ""
        if isinstance(target, dict) and "target" in target: data["target"]=target["target"]
        elif isinstance(target, str): data["target"]=target
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
    chat_id=m.chat.id
    args=m.text.split(" ",1);cmd=args[0].replace("/","").split("@")[0]
    if cmd=="adduser":
        a=m.text.split()
        if len(a)<3:
            mm=bot.send_message(chat_id,"❌ /adduser ID LEVEL\nEx: /adduser 123456 VIP")
            store_and_cleanup(chat_id, mm.message_id); return
        uid=a[1].strip().replace("@","");lvl=a[2].lower().strip();days=None
        if len(a)>=4:
            try: days=int(a[3])
            except: days=None
        mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
        if lvl not in mp:
            mm=bot.send_message(chat_id,f"❌ Invalid {lvl}"); store_and_cleanup(chat_id, mm.message_id); return
        d=load_db();final_level="none" if lvl=="free" else ("vip" if lvl=="lifetime" else lvl);verified=lvl!="free"
        d[uid]={"total":mp[lvl],"level":final_level,"verified":verified,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        if lvl=="free": d[uid]["level"]="none"
        if days: d[uid]["expires_at"]=(datetime.now()+timedelta(days=days)).isoformat()
        elif lvl=="lifetime": d[uid]["expires_at"]="lifetime"
        save(d)
        mm=bot.send_message(chat_id,f"✅ Added {uid} as {lvl.upper()} 👑")
        store_and_cleanup(chat_id, mm.message_id); return
    if cmd=="ban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=True;save(d)
        mm=bot.send_message(chat_id,"🚫 Banned"); store_and_cleanup(chat_id, mm.message_id); return
    if cmd=="unban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=False;save(d)
        mm=bot.send_message(chat_id,"✅ Unbanned"); store_and_cleanup(chat_id, mm.message_id); return

def signal_keyboard():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
    k.add(types.InlineKeyboardButton("🔥 Next Signal",callback_data="sel_market"))
    return k@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    try:
        tid=str(c.from_user.id);d=c.data;chat_id=c.message.chat.id;lvl=get_lvl(tid)
        if not (d.startswith("del_") or d.startswith("broad_") or d.startswith("addlvl_")):
            try: bot.delete_message(chat_id,c.message.message_id)
            except: pass
        if d in ["res_win","res_loss"]:
            dbb=load_db();ud=dbb.get(tid);adm=load_admin()
            if d=="res_win":
                ud["wins"]=ud.get("wins",0)+1;ud["win_streak"]=ud.get("win_streak",0)+1;ud["loss_streak"]=0;dbb[tid]=ud;save(dbb)
                adm["total_wins"]=adm.get("total_wins",0)+1;save_admin(adm)
                mm=bot.send_message(chat_id, f"✅ WIN! Streak {ud['win_streak']}!", reply_markup=signal_keyboard())
                store_and_cleanup(chat_id, mm.message_id); return
            else:
                ud["losses"]=ud.get("losses",0)+1;ud["loss_streak"]=ud.get("loss_streak",0)+1;ud["win_streak"]=0;dbb[tid]=ud;save(dbb)
                adm["total_losses"]=adm.get("total_losses",0)+1;save_admin(adm);ls=ud.get("loss_streak",0)
                if ls>=6:
                    mm=bot.send_message(chat_id, f"⚠️ {ls} LOSS STREAK STOP!", reply_markup=signal_keyboard())
                    store_and_cleanup(chat_id, mm.message_id); return
                mm=bot.send_message(chat_id, f"❌ Loss streak {ls} Next WIN!", reply_markup=signal_keyboard())
                store_and_cleanup(chat_id, mm.message_id); return
        if d=="admin" and tid==OWNER:
            k=types.InlineKeyboardMarkup(row_width=2)
            k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
            k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
            k.add(types.InlineKeyboardButton("➕ Add User 👑",callback_data="ad_adduser"))
            k.add(types.InlineKeyboardButton("💰 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
            k.add(types.InlineKeyboardButton("🔒 Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🏆 WR",callback_data="ad_wr"))
            mm=bot.send_message(chat_id,f"👑 ADMIN V11 👑\n👥 Users {len(load_db())}",reply_markup=k)
            store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and d.startswith("ad_"):
            if d=="ad_users":
                txt="👥 Users:\n"
                for uid,u in list(load_db().items())[:20]: txt+=f"{uid} {u.get('level')} ${u.get('total')}\n"
                mm=bot.send_message(chat_id,txt); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_adduser":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="addlvl_free"))
                kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="addlvl_starter"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="addlvl_pro"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="addlvl_vip"))
                kb.add(types.InlineKeyboardButton("💎 LIFETIME ♾️",callback_data="addlvl_lifetime"))
                mm=bot.send_message(chat_id,"➕ SELECT LEVEL:",reply_markup=kb); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_stats":
                dd=load_db();tot=sum(u.get('total',0) for u in dd.values());ver=sum(1 for u in dd.values() if u.get('verified'))
                mm=bot.send_message(chat_id,f"📊 U:{len(dd)} V:{ver} ${tot}"); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_wr":
                adm=load_admin();wins=adm.get('total_wins',0);losses=adm.get('total_losses',0);total=wins+losses;wr=round(wins/total*100,1) if total>0 else 0
                mm=bot.send_message(chat_id,f"🏆 WR ✅ {wins} ❌ {losses} {wr}%"); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_deps":
                dd=load_db();txt="💰 Deposits:\n"
                for uid,u in dd.items():
                    if u.get('total',0)>0: txt+=f"{uid} ${u.get('total')}\n"
                mm=bot.send_message(chat_id,txt or "None"); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_reset":
                dd=load_db()
                for u in dd.values(): u["today"]=0;u["date"]=str(date.today())
                save(dd);mm=bot.send_message(chat_id,"🔄 Reset Done"); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_broad":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL"))
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="broad_FREE"))
                kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="broad_STARTER"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="broad_PRO"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="broad_VIP"))
                kb.add(types.InlineKeyboardButton("💰 ALL VIPs",callback_data="broad_ALLVIP"))
                mm=bot.send_message(chat_id,"🎯 Select target:",reply_markup=kb); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_ban": mm=bot.send_message(chat_id,"🚫 /ban ID /unban ID"); store_and_cleanup(chat_id, mm.message_id); return
            if d=="ad_sec": mm=bot.send_message(chat_id,"🔒 Log empty"); store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and d.startswith("addlvl_"):
            level=d.replace("addlvl_","");add_pending[tid]=level
            mm=bot.send_message(chat_id,f"✅ Level {level.upper()} selected!\nSEND User ID:"); store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and d.startswith("broad_"):
            target=d.replace("broad_","");broadcast_data[tid]={"target": target, "type": "pending"}
            mm=bot.send_message(chat_id,f"🎯 Target {target} ✅\nSEND broadcast msg:"); store_and_cleanup(chat_id, mm.message_id); return
        if tid==OWNER and d.startswith("del_"):
            content=broadcast_data.get(tid)
            if not content or content.get("type")=="pending":
                mm=bot.send_message(chat_id,"❌ No broadcast content"); store_and_cleanup(chat_id, mm.message_id); return
            target=content["target"];days_str=d.replace("del_","");delete_days=None
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
                mm=bot.send_message(chat_id,f"✅ Broadcast {cnt} users 🎯 {target}\n⏰ Will auto-delete in {delete_days} days for USERS (your chat cleaned, broadcast stays till then)"); store_and_cleanup(chat_id, mm.message_id)
            else:
                mm=bot.send_message(chat_id,f"✅ Broadcast {cnt} users 🎯 {target}\n♾️ No auto-delete - stays forever"); store_and_cleanup(chat_id, mm.message_id)
            if tid in broadcast_data: del broadcast_data[tid]
            return
        if d=="dep":
            k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("💰 Deposit",url=LINK+"?click_id="+tid))
            mm=bot.send_message(chat_id,f"💰 DEPOSIT {LINK}?click_id={tid}",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d=="upg":
            u=ensure(tid);cur_total=u.get('total',0)
            k=types.InlineKeyboardMarkup()
            k.add(types.InlineKeyboardButton("⭐ STARTER $20",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("💎 PRO $50",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("👑 VIP $100",url=LINK+"?click_id="+tid))
            mm=bot.send_message(chat_id,f"🚀 UPGRADE Level:{lvl.upper()} Deposit:${cur_total}",reply_markup=k)
            store_and_cleanup(chat_id, mm.message_id);return
        if d=="how": mm=bot.send_message(chat_id,"❓ HOW: Register Deposit /start Get Signal"); store_and_cleanup(chat_id, mm.message_id);return
        if d in ["bal","status"]:
            u=ensure(tid);lim_txt="♾️" if lvl=="vip" else "20" if lvl=="starter" else "100" if lvl=="pro" else "3"
            mm=bot.send_message(chat_id,f"👤 Level:{lvl.upper()} Deposit:${u.get('total',0)} Today:{u.get('today',0)}/{lim_txt}"); store_and_cleanup(chat_id, mm.message_id);return
        if d=="sup": mm=bot.send_message(chat_id,"📞 Support @YourSupport"); store_and_cleanup(chat_id, mm.message_id);return
        if d=="sel_market":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
            mm=bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d=="m_real":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
            mm=bot.send_message(chat_id,"💹 REAL 15",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d=="m_otc":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
            mm=bot.send_message(chat_id,"📊 OTC 30",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d=="real_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in REAL: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_REAL"))
            mm=bot.send_message(chat_id,"✋ Pick Pair",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d=="otc_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[:15]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("➡️ Next 15",callback_data="otc_manual2"))
            mm=bot.send_message(chat_id,"✋ OTC 1/2",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d=="otc_manual2":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[15:]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("⬅️ Back",callback_data="otc_manual"))
            mm=bot.send_message(chat_id,"✋ OTC 2/2",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d.startswith("pair_"):
            rest=d[5:];pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}"); store_and_cleanup(chat_id, mm.message_id);return
            k=types.InlineKeyboardMarkup(row_width=4)
            k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5"))
            mm=bot.send_message(chat_id,f"💹 {pair} Pick Expiry:",reply_markup=k); store_and_cleanup(chat_id, mm.message_id);return
        if d in ["real_auto","otc_auto"]:
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}"); store_and_cleanup(chat_id, mm.message_id);return
            pairs=OTC if d.startswith("otc_") else REAL
            pair=random.choice(pairs);exp=random.choice(EXP)
            sig,rsi,trend,conf=get_sig(pair, exp, lvl);inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% 💹 {pair} {'📈 BUY' if 'BUY' in sig else '📉 SELL'} {sig} Exp {exp} RSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard())
            store_and_cleanup(chat_id, mm.message_id);return
        if d.startswith("sig_"):
            tmp=d[4:];idx=tmp.rfind("_M");pair=tmp[:idx];exp=tmp[idx+1:]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}"); store_and_cleanup(chat_id, mm.message_id);return
            sig,rsi,trend,conf=get_sig(pair, exp, lvl);inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% {pair} {'📈 BUY' if 'BUY' in sig else '📉 SELL'} {sig} Exp {exp} RSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard())
            store_and_cleanup(chat_id, mm.message_id);return
    except Exception as e: print(f"CB ERR {e}")
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
