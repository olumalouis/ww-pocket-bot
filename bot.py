import os, json, random, time, hashlib, hmac, telebot, threading
from telebot import types
from datetime import date, datetime, timedelta
from flask import Flask, request, abort
TOKEN=os.getenv("BOT_TOKEN","").strip()
LINK=os.getenv("LINK","https://poafficl.com/click")
SECRET=os.getenv("SECRET","kazi_secret")
OWNER=str(os.getenv("OWNER_ID","")).strip()
DB="/tmp/db.json"
ADMIN_DB="/tmp/admin_stats.json"
BROADCAST_DB="/tmp/broadcast.json"
REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","EUR/JPY","GBP/JPY","EUR/AUD","USD/CHF","NZD/USD","EUR/CAD","GBP/CAD","AUD/JPY","GBP/AUD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/GBP OTC","USD/CAD OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","EUR/AUD OTC","USD/CHF OTC","NZD/USD OTC","EUR/CAD OTC","GBP/CAD OTC","AUD/CAD OTC","GBP/AUD OTC","EUR/NZD OTC","AUD/NZD OTC","CHF/JPY OTC","EUR/CHF OTC","GBP/CHF OTC","AUD/CHF OTC","NZD/JPY OTC","CAD/JPY OTC","CAD/CHF OTC","USD/BRL OTC","USD/INR OTC","USD/TRY OTC","USD/ZAR OTC","USD/MXN OTC"]
EXP=["M1","M2","M3","M5"]
bot=telebot.TeleBot(TOKEN, threaded=False)
app=Flask(__name__)
for p,dv in [(DB,{}),(ADMIN_DB,{"total_wins":0,"total_losses":0}),(BROADCAST_DB,[])]:
    if not os.path.exists(p):
        with open(p,"w") as f: json.dump(dv,f)
def load_db():
    try:
        with open(DB,"r") as f: return json.load(f)
    except: return {}
def save(d):
    with open(DB,"w") as f: json.dump(d,f)
def load_admin():
    try:
        with open(ADMIN_DB,"r") as f: return json.load(f)
    except: return {"total_wins":0,"total_losses":0}
def save_admin(d):
    with open(ADMIN_DB,"w") as f: json.dump(d,f)
def load_broadcast():
    try:
        with open(BROADCAST_DB,"r") as f: return json.load(f)
    except: return []
def save_broadcast(d):
    with open(BROADCAST_DB,"w") as f: json.dump(d,f)

broadcast_data={}
add_pending={}
msg_hist={} # chat_id -> list of bot msg ids to auto-delete

def cleanup_old_messages(chat_id, keep_id=None):
    """Delete all previous bot messages, keep only latest and broadcast scheduled"""
    try:
        if chat_id not in msg_hist: return
        # Don't delete broadcast scheduled messages
        b_list=load_broadcast()
        protected_ids=set([b["msg_id"] for b in b_list if b["chat_id"]==chat_id])
        for mid in msg_hist[chat_id][:]: # copy
            if mid==keep_id: continue
            if mid in protected_ids: continue
            try:
                bot.delete_message(chat_id, mid)
                time.sleep(0.03)
            except: pass
        # Keep only the latest one
        if keep_id:
            msg_hist[chat_id]=[keep_id]
        else:
            msg_hist[chat_id]=[]
    except: pass

def store_and_cleanup(chat_id, msg_id):
    if chat_id not in msg_hist: msg_hist[chat_id]=[]
    msg_hist[chat_id].append(msg_id)
    # Keep history small, but DON'T delete yet - will delete on next command
    if len(msg_hist[chat_id])>30:
        msg_hist[chat_id]=msg_hist[chat_id][-30:]

def ensure(uid):
    uid=str(uid); d=load_db()
    if uid not in d:
        d[uid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        save(d)
    u=d[uid]
    if u.get("date")!=str(date.today()):
        u["today"]=0;u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0;u["date"]=str(date.today());save(d)
    if uid==OWNER and OWNER!="": u["level"]="vip";u["verified"]=True;save(d)
    return u
def get_lvl(uid): return ensure(uid).get("level","none")
def check_limit(uid,lvl):
    u=ensure(uid);cur=u.get("today",0)
    lim=9999 if lvl=="vip" else 100 if lvl=="pro" else 20 if lvl=="starter" else 3
    return cur>=lim,cur,lim
def inc(uid):
    d=load_db();u=d.get(str(uid));u["today"]=u.get("today",0)+1;d[str(uid)]=u;save(d)
def get_sig(pair,exp,lvl):
    rsi=random.uniform(28,72)
    sig="SELL" if rsi>65 else "BUY" if rsi<35 else random.choice(["BUY","SELL"])
    trend="UP 📈" if "BUY" in sig else "DOWN 📉"
    conf=random.randint(75,85) if lvl=="vip" else random.randint(65,75) if lvl=="pro" else random.randint(65,70) if lvl=="starter" else random.randint(55,65)
    return sig,rsi,trend,conf

@app.route("/", methods=["GET","POST"])
@app.route("/webhook", methods=["GET","POST"])
def wh():
    if request.method=="GET": return "KAZI V11 AUTO-DELETE ✅"
    try:
        js=request.get_data().decode("utf-8")
        if js:
            upd=telebot.types.Update.de_json(js)
            bot.process_new_updates([upd])
    except Exception as e: print(f"WH ERR {e}")
    return "OK"

@app.route("/postback")
def pb():
    sig=request.args.get("sig","");cid=request.args.get("click_id","");s=request.args.get("sum","0")
    if not cid: abort(400)
    calc=hmac.new(SECRET.encode(), cid.encode(), hashlib.sha256).hexdigest()[:10]
    if sig!="" and sig!=calc: abort(403)
    try: sv=float(s)
    except: sv=0
    d=load_db();u=d.get(cid,{"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0})
    u["total"]=u.get("total",0)+sv;tot=u["total"];lvl="none"
    if tot>=100: lvl="vip"
    elif tot>=50: lvl="pro"
    elif tot>=20: lvl="starter"
    order={"none":0,"starter":1,"pro":2,"vip":3}
    if order.get(lvl,0)>order.get(u.get("level","none"),0): u["level"]=lvl
    if lvl!="none": u["verified"]=True
    d[cid]=u;save(d)
    try: bot.send_message(cid, f"✅ DEPOSIT ${sv} Total ${tot} Level {u.get('level').upper()}!")
    except: pass
    return "OK"

def auto_delete_worker():
    while True:
        try:
            lst=load_broadcast();now=datetime.now();new_lst=[]
            for item in lst:
                try:
                    del_at=datetime.fromisoformat(item["delete_at"])
                    if now>=del_at:
                        try: bot.delete_message(item["chat_id"], item["msg_id"])
                        except: pass
                    else: new_lst.append(item)
                except: new_lst.append(item)
            if len(new_lst)!=len(lst): save_broadcast(new_lst)
        except: pass
        time.sleep(1800) # check every 30min
threading.Thread(target=auto_delete_worker, daemon=True).start()

# ALWAYS REPLIES FIRST, THEN CLEANS OLD
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid=str(m.from_user.id); chat_id=m.chat.id
    # Clear pending states
    if uid in broadcast_data: del broadcast_data[uid]
    if uid in add_pending: del add_pending[uid]
    u=ensure(uid)
    if u.get("banned"):
        mm=bot.send_message(chat_id,"🚫 Banned")
        store_and_cleanup(chat_id, mm.message_id)
        # Delete old after sending
        threading.Thread(target=cleanup_old_messages, args=(chat_id, mm.message_id), daemon=True).start()
        return
    lvl=get_lvl(uid)
    if not u.get("verified"):
        k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("📝 Register",url=LINK+"?click_id="+uid))
        mm=bot.send_message(chat_id,f"👋 Welcome {m.from_user.first_name}!\nRegister:\n{LINK}?click_id={uid}",reply_markup=k)
        store_and_cleanup(chat_id, mm.message_id)
        threading.Thread(target=cleanup_old_messages, args=(chat_id, mm.message_id), daemon=True).start()
        return
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🚀 Get Signal 🔥",callback_data="sel_market"))
    k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("❓ How",callback_data="how"))
    k.add(types.InlineKeyboardButton("👤 Status",callback_data="status"),types.InlineKeyboardButton("📞 Support",callback_data="sup"))
    k.add(types.InlineKeyboardButton("🚀 Upgrade",callback_data="upg"))
    if uid==OWNER: k.add(types.InlineKeyboardButton("👑 Admin",callback_data="admin"))
    mm=bot.send_message(chat_id,f"👋 Welcome {m.from_user.first_name}!\n👑 {lvl.upper()} 📊 Today {u.get('today',0)}\n🔥 Ready?",reply_markup=k)
    store_and_cleanup(chat_id, mm.message_id)
    # AUTO DELETE OLD MESSAGES AFTER replying (keep new one)
    threading.Thread(target=cleanup_old_messages, args=(chat_id, mm.message_id), daemon=True).start()

@bot.message_handler(commands=["clearme","clear"])
def clearme(m):
    chat_id=m.chat.id; uid=str(m.from_user.id)
    if uid in broadcast_data: del broadcast_data[uid]
    if uid in add_pending: del add_pending[uid]
    mm=bot.send_message(chat_id,"✅ Cleared! /start")
    store_and_cleanup(chat_id, mm.message_id)
    threading.Thread(target=cleanup_old_messages, args=(chat_id, mm.message_id), daemon=True).start()
    @bot.message_handler(content_types=['text','photo','video','document','animation'], func=lambda m: str(m.from_user.id)==OWNER and (str(m.from_user.id) in broadcast_data or str(m.from_user.id) in add_pending) and not (m.text and m.text.startswith("/")))
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
    return k
    @bot.callback_query_handler(func=lambda c: True)
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
