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
if not os.path.exists(DB):
    with open(DB,"w") as f: json.dump({},f)
if not os.path.exists(ADMIN_DB):
    with open(ADMIN_DB,"w") as f: json.dump({"total_wins":0,"total_losses":0},f)
if not os.path.exists(BROADCAST_DB):
    with open(BROADCAST_DB,"w") as f: json.dump([],f)
def load_db():
    try:
        with open(DB,"r") as f: return json.load(f)
    except: return {}
def save(d):
    with open(DB,"w") as f: json.dump(d,f)
    global db
    db=d
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
db=load_db()
broadcast_pending={}
broadcast_content_pending={}
adduser_pending={}
sec_log=[]
msg_history={}
def cleanup_chat(chat_id):
    try:
        if chat_id in msg_history:
            for mid in msg_history[chat_id][-15:]:
                try: bot.delete_message(chat_id, mid)
                except: pass
            msg_history[chat_id]=[]
    except: pass
def store_msg(chat_id, mid):
    try:
        if chat_id not in msg_history: msg_history[chat_id]=[]
        msg_history[chat_id].append(mid)
        if len(msg_history[chat_id])>20:
            msg_history[chat_id]=msg_history[chat_id][-20:]
    except: pass
def ensure(uid):
    uid=str(uid)
    global db
    db=load_db()
    if uid not in db:
        db[uid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        save(db)
    u=db[uid]
    if u.get("date")!=str(date.today()):
        u["today"]=0;u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0
        u["date"]=str(date.today());save(db)
    if uid==OWNER and OWNER!="":
        u["level"]="vip";u["verified"]=True;save(db)
    return u
def get_lvl(uid): return ensure(uid).get("level","none")
def check_limit(uid,lvl):
    u=ensure(uid);cur=u.get("today",0)
    if lvl=="starter": lim=20
    elif lvl=="pro": lim=100
    elif lvl=="vip": lim=9999
    else: lim=3
    return cur>=lim,cur,lim
def inc(uid):
    u=ensure(uid);u["today"]=u.get("today",0)+1;db[str(uid)]=u;save(db)
def get_real_signal(pair,exp,lvl):
    rsi=random.uniform(28,72)
    sig="SELL" if rsi>65 else "BUY" if rsi<35 else random.choice(["BUY","SELL"])
    trend="UP 📈" if "BUY" in sig else "DOWN 📉"
    conf=random.randint(75,85) if lvl=="vip" else random.randint(65,75) if lvl=="pro" else random.randint(65,70) if lvl=="starter" else random.randint(55,65)
    return sig,rsi,trend,conf
@app.route("/", methods=["GET","POST"])
@app.route("/webhook", methods=["GET","POST"])
@app.route("/bot", methods=["GET","POST"])
def main_webhook():
    if request.method=="GET": return "OK KAZI V10 FINAL 🔥"
    try:
        js=request.get_data().decode("utf-8")
        if not js: return "OK"
        upd=telebot.types.Update.de_json(js)
        bot.process_new_updates([upd])
    except Exception as e: print(f"ERR {e}")
    return "OK"
@app.route("/postback")
def postback():
    sig=request.args.get("sig","");click_id=request.args.get("click_id","");sum_val=request.args.get("sum","0")
    if not click_id: abort(400)
    calc=hmac.new(SECRET.encode(), click_id.encode(), hashlib.sha256).hexdigest()[:10]
    if sig!="" and sig!=calc: abort(403)
    try: s=float(sum_val)
    except: s=0
    d=load_db()
    u=d.get(click_id,{"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0})
    u["total"]=u.get("total",0)+s;total=u["total"];lvl="none"
    if total>=100: lvl="vip"
    elif total>=50: lvl="pro"
    elif total>=20: lvl="starter"
    order={"none":0,"starter":1,"pro":2,"vip":3}
    old_lvl=u.get("level","none")
    if order.get(lvl,0)>order.get(old_lvl,0): u["level"]=lvl
    if lvl!="none": u["verified"]=True
    d[click_id]=u;save(d)
    try:
        if order.get(lvl,0)>order.get(old_lvl,0):
            m=bot.send_message(click_id, f"✅ DEPOSIT CONFIRMED ${s} 💰 Total ${total} 👑 UPGRADED to {u.get('level').upper()}! 🔥")
            store_msg(click_id, m.message_id)
        else:
            m=bot.send_message(click_id, f"✅ DEPOSIT CONFIRMED ${s} 💰 Total ${total} Level {u.get('level').upper()} 👑")
            store_msg(click_id, m.message_id)
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
        time.sleep(3600)
threading.Thread(target=auto_delete_worker, daemon=True).start()
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid=str(m.from_user.id)
    cleanup_chat(m.chat.id)
    if uid==OWNER:
        if uid in broadcast_pending: del broadcast_pending[uid]
        if uid in adduser_pending: del adduser_pending[uid]
        if uid in broadcast_content_pending: del broadcast_content_pending[uid]
    u=ensure(uid)
    if u.get("banned"):
        mm=bot.send_message(m.chat.id,"🚫 Banned");store_msg(m.chat.id, mm.message_id);return
    lvl=get_lvl(uid)
    if not u.get("verified"):
        k=types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("📝 Register Now",url=LINK+"?click_id="+uid))
        mm=bot.send_message(m.chat.id,f"👋 Welcome {m.from_user.first_name}!\n\n🔥 KAZI SIGNALS V9.5 🔥\n\n👉 Register First:\n{LINK}?click_id={uid}",reply_markup=k)
        store_msg(m.chat.id, mm.message_id);return
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🚀 Get Signal 🔥",callback_data="sel_market"))
    k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("❓ How",callback_data="how"))
    k.add(types.InlineKeyboardButton("👤 Status",callback_data="status"),types.InlineKeyboardButton("📞 Support",callback_data="sup"))
    k.add(types.InlineKeyboardButton("🚀 Upgrade",callback_data="upg"))
    if uid==OWNER and OWNER!="": k.add(types.InlineKeyboardButton("👑 Admin",callback_data="admin"))
    mm=bot.send_message(m.chat.id,f"👋 Welcome {m.from_user.first_name}!\n\n👑 Level: {lvl.upper()}\n📊 Today: {u.get('today',0)}\n\n🔥 Ready to Trade?",reply_markup=k)
    store_msg(m.chat.id, mm.message_id)
@bot.message_handler(commands=["clearme"])
def clearme(m):
    cleanup_chat(m.chat.id)
    uid=str(m.from_user.id);u=ensure(uid)
    u["today"]=0;u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0
    db[uid]=u;save(db)
    mm=bot.send_message(m.chat.id,"✅ Reset done! 🔄");store_msg(m.chat.id, mm.message_id)
# FIXED FILTER - ignores /commands so /start always works
@bot.message_handler(content_types=['text','photo','video','document','animation'], func=lambda m: str(m.from_user.id)==OWNER and (str(m.from_user.id) in broadcast_pending or str(m.from_user.id) in adduser_pending) and not (m.text and m.text.startswith("/")))
def owner_pending_handler(m):
    tid=str(m.from_user.id)
    if tid in adduser_pending:
        try:
            level=adduser_pending.get(tid);txt=m.text or "";uid_input=txt.strip().replace("@","").split()[0] if txt else ""
            if not uid_input.isdigit():
                mm=bot.send_message(m.chat.id,"❌ Send NUMERIC ID only!\nEx: 7123456789");store_msg(m.chat.id, mm.message_id);return
            uid=uid_input;d=load_db();mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
            lvl_clean=level.lower().split("_")[0]
            if lvl_clean not in mp:
                mm=bot.send_message(m.chat.id,"❌ Invalid level");store_msg(m.chat.id, mm.message_id);del adduser_pending[tid];return
            total_val=mp[lvl_clean];final_level="none" if lvl_clean=="free" else ("vip" if lvl_clean=="lifetime" else lvl_clean);verified=lvl_clean!="free"
            d[uid]={"total":total_val,"level":final_level,"verified":verified,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
            if lvl_clean=="free": d[uid]["level"]="none"
            if lvl_clean=="lifetime": d[uid]["expires_at"]="lifetime"
            save(d);del adduser_pending[tid]
            mm=bot.send_message(m.chat.id,f"✅ Added {uid} as {lvl_clean.upper()} 👑 Level={final_level.upper()}");store_msg(m.chat.id, mm.message_id)
        except Exception as e:
            mm=bot.send_message(m.chat.id,f"❌ Error: {e}");store_msg(m.chat.id, mm.message_id)
        return
    if tid in broadcast_pending:
        target=broadcast_pending.get(tid);data={"target": target}
        if m.content_type=="photo": data["type"]="photo";data["file_id"]=m.photo[-1].file_id;data["caption"]=m.caption or ""
        elif m.content_type=="video": data["type"]="video";data["file_id"]=m.video.file_id;data["caption"]=m.caption or ""
        elif m.content_type=="document": data["type"]="document";data["file_id"]=m.document.file_id;data["caption"]=m.caption or ""
        elif m.content_type=="animation": data["type"]="animation";data["file_id"]=m.animation.file_id;data["caption"]=m.caption or ""
        else: data["type"]="text";data["text"]=m.text or "";data["caption"]=m.text or ""
        broadcast_content_pending[tid]=data;del broadcast_pending[tid]
        k=types.InlineKeyboardMarkup(row_width=2)
        k.add(types.InlineKeyboardButton("♾️ No Delete",callback_data="del_none"))
        k.add(types.InlineKeyboardButton("🗓️ 1 Week",callback_data="del_7"),types.InlineKeyboardButton("📅 1 Month",callback_data="del_30"))
        k.add(types.InlineKeyboardButton("📆 3 Months",callback_data="del_90"),types.InlineKeyboardButton("🗓️ 6 Months",callback_data="del_180"))
        k.add(types.InlineKeyboardButton("📅 1 Year",callback_data="del_365"))
        mm=bot.send_message(m.chat.id,f"✅ Message saved! Type: {data['type']}\n🎯 Target: {target}\n\n⏰ Select auto-delete time:",reply_markup=k)
        store_msg(m.chat.id, mm.message_id);return@bot.message_handler(commands=["adduser","broadcast","ban","unban"])
def admin_cmds(m):
    if str(m.from_user.id)!=OWNER: return
    cleanup_chat(m.chat.id)
    if str(m.from_user.id) in broadcast_pending: del broadcast_pending[str(m.from_user.id)]
    if str(m.from_user.id) in adduser_pending: del adduser_pending[str(m.from_user.id)]
    args=m.text.split(" ",1);cmd=args[0].replace("/","").split("@")[0]
    if cmd=="adduser":
        a=m.text.split()
        if len(a)<3:
            mm=bot.send_message(m.chat.id,"❌ Usage:\n/adduser ID LEVEL [DAYS]\nLevels: FREE, STARTER, PRO, VIP, LIFETIME\nEx:\n/adduser 123456 VIP\n/adduser 123456 PRO 30")
            store_msg(m.chat.id, mm.message_id);return
        uid=a[1].strip().replace("@","");lvl=a[2].lower().strip();days=None
        if len(a)>=4:
            try: days=int(a[3])
            except: days=None
        mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
        if lvl not in mp:
            mm=bot.send_message(m.chat.id,f"❌ Invalid {lvl}");store_msg(m.chat.id, mm.message_id);return
        d=load_db();final_level="none" if lvl=="free" else ("vip" if lvl=="lifetime" else lvl);verified=lvl!="free"
        d[uid]={"total":mp[lvl],"level":final_level,"verified":verified,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        if lvl=="free": d[uid]["level"]="none"
        if days: d[uid]["expires_at"]=(datetime.now()+timedelta(days=days)).isoformat()
        elif lvl=="lifetime": d[uid]["expires_at"]="lifetime"
        save(d);mm=bot.send_message(m.chat.id,f"✅ Added {uid} as {lvl.upper()} 👑 Level={final_level.upper()}");store_msg(m.chat.id, mm.message_id);return
    if cmd=="broadcast" and len(args)>1:
        cnt=0;d=load_db()
        for uid in list(d.keys()):
            try: bot.send_message(uid,f"{args[1]}");cnt+=1;time.sleep(0.05)
            except: pass
        mm=bot.send_message(m.chat.id,f"✅ Sent {cnt} 📢");store_msg(m.chat.id, mm.message_id)
    if cmd=="ban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=True;save(d)
        mm=bot.send_message(m.chat.id,"🚫 Banned");store_msg(m.chat.id, mm.message_id)
    if cmd=="unban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=False;save(d)
        mm=bot.send_message(m.chat.id,"✅ Unbanned");store_msg(m.chat.id, mm.message_id)

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
            try:
                bot.delete_message(chat_id,c.message.message_id)
                if chat_id in msg_history and c.message.message_id in msg_history[chat_id]:
                    msg_history[chat_id].remove(c.message.message_id)
            except: pass
        if d in ["res_win","res_loss"]:
            u=ensure(tid);adm=load_admin()
            if d=="res_win":
                u["wins"]=u.get("wins",0)+1;u["win_streak"]=u.get("win_streak",0)+1;u["loss_streak"]=0;db[tid]=u;save(db)
                adm["total_wins"]=adm.get("total_wins",0)+1;save_admin(adm)
                msgs=[f"✅ BOOM! WIN! 🔥💰\n🏆 Streak: {u['win_streak']} Wins!",f"✅ PERFECT WIN! 💎🔥\n📈 {u['win_streak']} in a row!",f"✅ KAZI WIN! 👑💸\n🔥 Win streak {u['win_streak']}!",f"✅ BANG! WIN! 🚀\n💰 {u['win_streak']} Wins straight!"]
                mm=bot.send_message(chat_id, random.choice(msgs), reply_markup=signal_keyboard());store_msg(chat_id, mm.message_id);return
            else:
                u["losses"]=u.get("losses",0)+1;u["loss_streak"]=u.get("loss_streak",0)+1;u["win_streak"]=0;db[tid]=u;save(db)
                adm["total_losses"]=adm.get("total_losses",0)+1;save_admin(adm);ls=u.get("loss_streak",0)
                if ls>=6:
                    mm=bot.send_message(chat_id, f"⚠️ WARNING! {ls} LOSS STREAK 🚫\n\n🧠 Boss, STOP trading now!\n📉 Market bad today!\n☕️ Rest 1 hour!\n🔄 Come back fresh!", reply_markup=signal_keyboard())
                    store_msg(chat_id, mm.message_id);return
                if ls==3: msg=f"❌ 3 Losses 😤\n🧠 Don't revenge trade!\n💪 Next is WIN!"
                elif ls==4: msg=f"❌ 4 Losses 💔\n⚠️ Slow down!\n🔥 We recover!"
                elif ls==5: msg=f"❌ 5 Losses! 🚨\n🛑 Almost limit!\n🧘 Breathe!"
                else:
                    lmsgs=[f"❌ Loss, but learn! 📚\n💪 Streak {ls} - Next WIN!",f"❌ Not today! ⚔️\n🔥 {ls} loss - adapt!",f"❌ Small loss! 💸\n🚀 WIN coming!",f"❌ Oops! 📉\n💎 Stay focused!"]
                    msg=random.choice(lmsgs)
                mm=bot.send_message(chat_id, msg, reply_markup=signal_keyboard());store_msg(chat_id, mm.message_id);return
        if d=="admin" and tid==OWNER:
            k=types.InlineKeyboardMarkup(row_width=2)
            k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
            k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
            k.add(types.InlineKeyboardButton("➕ Add User 👑",callback_data="ad_adduser"))
            k.add(types.InlineKeyboardButton("💰 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
            k.add(types.InlineKeyboardButton("🔒 Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🏆 WR",callback_data="ad_wr"))
            mm=bot.send_message(chat_id,f"👑 ADMIN V10 👑\n👥 Users {len(load_db())}",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if tid==OWNER and d.startswith("ad_"):
            if d=="ad_users":
                txt="👥 Users:\n"
                for uid,u in list(load_db().items())[:20]: txt+=f"{uid} {u.get('level')} ${u.get('total')}\n"
                mm=bot.send_message(chat_id,txt);store_msg(chat_id, mm.message_id);return
            if d=="ad_adduser":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="addlvl_free"))
                kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="addlvl_starter"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="addlvl_pro"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="addlvl_vip"))
                kb.add(types.InlineKeyboardButton("💎 LIFETIME ♾️",callback_data="addlvl_lifetime"))
                mm=bot.send_message(chat_id,"➕ SELECT LEVEL:",reply_markup=kb);store_msg(chat_id, mm.message_id);return
            if d=="ad_stats":
                dd=load_db();tot=sum(u.get('total',0) for u in dd.values());ver=sum(1 for u in dd.values() if u.get('verified'))
                mm=bot.send_message(chat_id,f"📊 Stats\n👥 U:{len(dd)} ✅ V:{ver} 💰 ${tot}");store_msg(chat_id, mm.message_id);return
            if d=="ad_wr":
                adm=load_admin();wins=adm.get('total_wins',0);losses=adm.get('total_losses',0);total=wins+losses;wr=round(wins/total*100,1) if total>0 else 0
                mm=bot.send_message(chat_id,f"🏆 REAL WR\n✅ {wins} Wins ❌ {losses} Losses\n📊 WR: {wr}%");store_msg(chat_id, mm.message_id);return
            if d=="ad_deps":
                dd=load_db();txt="💰 Deposits:\n"
                for uid,u in dd.items():
                    if u.get('total',0)>0: txt+=f"{uid} ${u.get('total')}\n"
                mm=bot.send_message(chat_id,txt or "None");store_msg(chat_id, mm.message_id);return
            if d=="ad_reset":
                dd=load_db()
                for u in dd.values(): u["today"]=0;u["date"]=str(date.today())
                save(dd);mm=bot.send_message(chat_id,"🔄 Reset Done ✅");store_msg(chat_id, mm.message_id);return
            if d=="ad_broad":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL"))
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="broad_FREE"))
                kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="broad_STARTER"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="broad_PRO"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="broad_VIP"))
                kb.add(types.InlineKeyboardButton("💰 ALL VIPs",callback_data="broad_ALLVIP"))
                mm=bot.send_message(chat_id,"🎯 Select target:",reply_markup=kb);store_msg(chat_id, mm.message_id);return
            if d=="ad_ban": mm=bot.send_message(chat_id,"🚫 /ban ID /unban ID");store_msg(chat_id, mm.message_id);return
            if d=="ad_sec":
                txt="🔒 Log:\n"
                for s in sec_log[-10:]: txt+=f"{s.get('ip')} {s.get('status')}\n"
                mm=bot.send_message(chat_id,txt);store_msg(chat_id, mm.message_id);return
        if tid==OWNER and d.startswith("addlvl_"):
            level=d.replace("addlvl_","");adduser_pending[tid]=level
            mm=bot.send_message(chat_id,f"✅ Level {level.upper()} selected!\n\n📝 Now SEND User ID\nEx: 7123456789")
            store_msg(chat_id, mm.message_id)
            try: bot.delete_message(chat_id,c.message.message_id)
            except: pass
            return
        if tid==OWNER and d.startswith("broad_"):
            target=d.replace("broad_","");broadcast_pending[tid]=target
            mm=bot.send_message(chat_id,f"🎯 Target {target} ✅\n\n📝 SEND message now:")
            store_msg(chat_id, mm.message_id)
            try: bot.delete_message(chat_id,c.message.message_id)
            except: pass
            return        if tid==OWNER and d.startswith("del_"):
            content=broadcast_content_pending.get(tid)
            if not content:
                mm=bot.send_message(chat_id,"❌ No broadcast pending");store_msg(chat_id, mm.message_id);return
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
                        if delete_at: b_list.append({"chat_id": uid, "msg_id": sent.message_id, "delete_at": delete_at.isoformat()})
                        time.sleep(0.05)
                    except: continue
            if delete_at:
                save_broadcast(b_list)
                mm=bot.send_message(chat_id,f"✅ Sent {cnt} users 🎯 {target}\n⏰ Delete in {delete_days} days!");store_msg(chat_id, mm.message_id)
            else:
                mm=bot.send_message(chat_id,f"✅ Sent {cnt} users 🎯 {target}\n♾️ No auto-delete");store_msg(chat_id, mm.message_id)
            if tid in broadcast_content_pending: del broadcast_content_pending[tid]
            try: bot.delete_message(chat_id,c.message.message_id)
            except: pass
            return
        if d=="dep":
            k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("💰 Register + Deposit",url=LINK+"?click_id="+tid))
            mm=bot.send_message(chat_id,f"💰 DEPOSIT NOW 👇\n{LINK}?click_id={tid}",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d=="upg":
            u=ensure(tid);cur_total=u.get('total',0)
            k=types.InlineKeyboardMarkup()
            k.add(types.InlineKeyboardButton("⭐ STARTER $20",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("💎 PRO $50 - POPULAR 🔥",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("👑 VIP $100 - BEST WR 85%",url=LINK+"?click_id="+tid))
            mm=bot.send_message(chat_id,f"🚀 UPGRADE PLAN\n\n👤 Status:\n👑 Level: {lvl.upper()}\n💰 Deposit: ${cur_total}\n📊 Today: {u.get('today',0)}/{'♾️' if lvl=='vip' else '20' if lvl=='starter' else '100' if lvl=='pro' else '3'}\n\n💎 PLANS:\n🆓 FREE $0 3/day 55-65% WR\n⭐ STARTER $20 20/day 65-70% WR\n💎 PRO $50 100/day 70-75% WR\n👑 VIP $100 UNLIMITED 75-85% WR\n\n⚡️ 90% choose PRO or VIP!\n💸 Deposit now!",reply_markup=k)
            store_msg(chat_id, mm.message_id);return
        if d=="how": mm=bot.send_message(chat_id,"❓ HOW V9.5\n1️⃣ Register\n2️⃣ Deposit\n3️⃣ /start\n4️⃣ Get Signal");store_msg(chat_id, mm.message_id);return
        if d in ["bal","status"]:
            u=ensure(tid);lim_txt="♾️" if lvl=="vip" else "20" if lvl=="starter" else "100" if lvl=="pro" else "3"
            mm=bot.send_message(chat_id,f"👤 STATUS\n👑 Level: {lvl.upper()}\n💰 Deposit: ${u.get('total',0)}\n📊 Today: {u.get('today',0)}/{lim_txt}\n🏆 Wins: {u.get('wins',0)} | ❌ Loss: {u.get('losses',0)}");store_msg(chat_id, mm.message_id);return
        if d=="sup": mm=bot.send_message(chat_id,"📞 Support @YourSupport");store_msg(chat_id, mm.message_id);return
        if d=="sel_market":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
            mm=bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d=="m_real":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
            mm=bot.send_message(chat_id,"💹 REAL 15 Market",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d=="m_otc":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
            mm=bot.send_message(chat_id,"📊 OTC 30 Market",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d=="real_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in REAL: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_REAL"))
            mm=bot.send_message(chat_id,"✋ MANUAL REAL Pick Pair 👇",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d=="otc_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[:15]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("➡️ Next 15",callback_data="otc_manual2"))
            mm=bot.send_message(chat_id,"✋ MANUAL OTC 1/2 👇",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d=="otc_manual2":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[15:]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("⬅️ Back",callback_data="otc_manual"))
            mm=bot.send_message(chat_id,"✋ MANUAL OTC 2/2 👇",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d.startswith("pair_"):
            rest=d[5:];pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}");store_msg(chat_id, mm.message_id);return
            k=types.InlineKeyboardMarkup(row_width=4)
            k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5"))
            mm=bot.send_message(chat_id,f"💹 Pair {pair}\n⏰ Pick Expiry:",reply_markup=k);store_msg(chat_id, mm.message_id);return
        if d in ["real_auto","otc_auto"]:
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}");store_msg(chat_id, mm.message_id);return
            pairs=OTC if d.startswith("otc_") else REAL
            pair=random.choice(pairs);exp=random.choice(EXP)
            sig,rsi,trend,conf=get_real_signal(pair, exp, lvl);inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% 💹\n📊 {pair}\n{'📈 BUY' if 'BUY' in sig else '📉 SELL'} {sig}\n⏰ Exp {exp}\n📉 RSI {rsi:.1f} {trend}\n📊 {cur+1}/{lim}",reply_markup=signal_keyboard())
            store_msg(chat_id, mm.message_id);return
        if d.startswith("sig_"):
            tmp=d[4:];idx=tmp.rfind("_M");pair=tmp[:idx];exp=tmp[idx+1:]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}");store_msg(chat_id, mm.message_id);return
            sig,rsi,trend,conf=get_real_signal(pair, exp, lvl);inc(tid)
            mm=bot.send_message(chat_id,f"🔥 SIGNAL {lvl.upper()} {conf}% 💹\n📊 Pair {pair}\n{'📈 BUY' if 'BUY' in sig else '📉 SELL'} Dir {sig}\n⏰ Exp {exp}\n📉 RSI {rsi:.1f} {trend}\n📊 {cur+1}/{lim}",reply_markup=signal_keyboard())
            store_msg(chat_id, mm.message_id);return
    except Exception as e: print(f"ERR {e}")
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
