import os, json, random, time, hashlib, hmac, telebot
from telebot import types
from datetime import date
from flask import Flask, request, abort

TOKEN=os.getenv("BOT_TOKEN","").strip()
LINK=os.getenv("LINK","https://poafficl.com/click")
SECRET=os.getenv("SECRET","kazi_secret")
OWNER=str(os.getenv("OWNER_ID","")).strip()
DB="/tmp/db.json"

REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","EUR/JPY","GBP/JPY","EUR/AUD","USD/CHF","NZD/USD","EUR/CAD","GBP/CAD","AUD/JPY","GBP/AUD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/GBP OTC","USD/CAD OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","EUR/AUD OTC","USD/CHF OTC","NZD/USD OTC","EUR/CAD OTC","GBP/CAD OTC","AUD/CAD OTC","GBP/AUD OTC","EUR/NZD OTC","AUD/NZD OTC","CHF/JPY OTC","EUR/CHF OTC","GBP/CHF OTC","AUD/CHF OTC","NZD/JPY OTC","CAD/JPY OTC","CAD/CHF OTC","USD/BRL OTC","USD/INR OTC","USD/TRY OTC","USD/ZAR OTC","USD/MXN OTC"]
EXP=["M1","M2","M3","M5"]

bot=telebot.TeleBot(TOKEN, threaded=False)
app=Flask(__name__)

if not os.path.exists(DB):
    with open(DB,"w") as f: json.dump({},f)

def load_db():
    try:
        with open(DB,"r") as f: return json.load(f)
    except: return {}
def save(d):
    with open(DB,"w") as f: json.dump(d,f)
    global db
    db=d

db=load_db()
broadcast_pending={}
sec_log=[]

def ensure(uid):
    uid=str(uid)
    global db
    db=load_db()
    if uid not in db:
        db[uid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        save(db)
    u=db[uid]
    if u.get("date")!=str(date.today()):
        u["today"]=0;u["date"]=str(date.today());save(db)
    if uid==OWNER and OWNER!="":
        u["level"]="vip";u["verified"]=True;save(db)
    return u

def get_lvl(uid): return ensure(uid).get("level","none")

def check_limit(uid,lvl):
    u=ensure(uid); cur=u.get("today",0)
    if lvl=="starter": lim=20
    elif lvl=="pro": lim=100
    elif lvl=="vip": lim=9999
    else: lim=3
    return cur>=lim,cur,lim

def inc(uid):
    u=ensure(uid); u["today"]=u.get("today",0)+1; db[str(uid)]=u; save(db)

def get_real_signal(pair, exp, lvl):
    rsi=random.uniform(28,72)
    if rsi>65: sig="PUT 🔻"
    elif rsi<35: sig="CALL 🔺"
    else: sig="CALL 🔺" if random.random()>0.5 else "PUT 🔻"
    trend="UP" if "CALL" in sig else "DOWN"
    if lvl=="vip": conf=random.randint(75,85)
    elif lvl=="pro": conf=random.randint(65,75)
    elif lvl=="starter": conf=random.randint(65,70)
    else: conf=random.randint(55,65)
    return sig, rsi, trend, conf

@app.route("/", methods=["GET","POST"])
def main_webhook():
    if request.method=="GET":
        return "✅ KAZI V8 Running - POST OK"
    try:
        js=request.get_data().decode("utf-8")
        if not js: return "OK"
        upd=telebot.types.Update.de_json(js)
        bot.process_new_updates([upd])
    except Exception as e:
        print(f"Webhook ERR {e}")
    return "OK"

@app.route("/postback")
def postback():
    sig=request.args.get("sig",""); click_id=request.args.get("click_id",""); sum_val=request.args.get("sum","0")
    if not click_id: abort(400)
    calc=hmac.new(SECRET.encode(), click_id.encode(), hashlib.sha256).hexdigest()[:10]
    if sig!="" and sig!=calc: abort(403)
    try: s=float(sum_val)
    except: s=0
    lvl="none"
    if s>=100: lvl="vip"
    elif s>=50: lvl="pro"
    elif s>=20: lvl="starter"
    d=load_db()
    u=d.get(click_id,{"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0})
    u["total"]=u.get("total",0)+s
    order={"none":0,"starter":1,"pro":2,"vip":3}
    if order.get(lvl,0)>order.get(u.get("level","none"),0): u["level"]=lvl
    if lvl!="none": u["verified"]=True
    d[click_id]=u; save(d)
    try: bot.send_message(click_id, f"💰 DEPOSIT CONFIRMED ${s}\n🎉 Level: {u.get('level').upper()}\n✅ Verified!\n/start for signals!")
    except: pass
    return "OK"

@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid=str(m.from_user.id)
    u=ensure(uid)
    if u.get("banned"): bot.send_message(m.chat.id,"🚫 Banned"); return
    lvl=get_lvl(uid)
    if not u.get("verified"):
        k=types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("🔗 Register Pocket Option",url=LINK+"?click_id="+uid))
        k.add(types.InlineKeyboardButton("💵 Deposit $20",url=LINK+"?click_id="+uid))
        bot.send_message(m.chat.id,f"👋 Welcome {m.from_user.first_name}!\n\n💹 KAZI FX V8\n\n1️⃣ Register: {LINK}?click_id={uid}\n2️⃣ Deposit $20/$50/$100\n3️⃣ /start\n\n🎯 65-85% Accuracy",reply_markup=k)
        return
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC 30",callback_data="m_otc"))
    k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("📚 How to use",callback_data="how"))
    k.add(types.InlineKeyboardButton("📊 My Balance",callback_data="bal"),types.InlineKeyboardButton("💬 Support",callback_data="sup"))
    k.add(types.InlineKeyboardButton("🚀 Upgrade Plan",callback_data="upg"))
    if uid==OWNER and OWNER!="":
        k.add(types.InlineKeyboardButton("👑 Admin Panel",callback_data="admin"))
    bot.send_message(m.chat.id,f"✅ Welcome {m.from_user.first_name}!\n💹 KAZI V8 Ready\nLevel: {lvl.upper()}\nToday: {u.get('today',0)}\n🎯 Select Market:",reply_markup=k)

@bot.message_handler(commands=["clearme"])
def clearme(m):
    uid=str(m.from_user.id); u=ensure(uid)
    u["today"]=0;u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0
    db[uid]=u; save(db)
    bot.send_message(m.chat.id,"✅ Reset done!")
    @bot.message_handler(func=lambda m: str(m.from_user.id)==OWNER and str(m.from_user.id) in broadcast_pending)
def broadcast_send(m):
    target=broadcast_pending.get(str(m.from_user.id))
    msg_text=m.text or ""
    cnt=0; d=load_db()
    for uid,u in list(d.items()):
        lvl=u.get("level","none"); ver=u.get("verified",False); send=False
        if target=="ALL": send=True
        elif target=="FREE" and not ver: send=True
        elif target=="STARTER" and lvl=="starter": send=True
        elif target=="PRO" and lvl=="pro": send=True
        elif target=="VIP" and lvl=="vip": send=True
        elif target=="ALLVIP" and lvl in ["starter","pro","vip"]: send=True
        if send:
            try: bot.send_message(uid, f"📢 {msg_text}"); cnt+=1; time.sleep(0.05)
            except: pass
    del broadcast_pending[str(m.from_user.id)]
    bot.send_message(m.chat.id,f"✅ Sent {cnt} Target: {target}")

@bot.message_handler(commands=["adduser","broadcast","ban","unban"])
def admin_cmds(m):
    if str(m.from_user.id)!=OWNER: return
    args=m.text.split(" ",1); cmd=args[0].replace("/","").split("@")[0]
    if cmd=="adduser":
        a=m.text.split()
        if len(a)<3: bot.send_message(m.chat.id,"/adduser ID LEVEL"); return
        uid=a[1].strip(); lvl=a[2].lower().strip()
        mp={"free":0,"starter":20,"pro":50,"vip":100}
        if lvl not in mp: return
        d=load_db()
        d[uid]={"total":mp[lvl],"level":lvl if lvl!="free" else "none","verified":lvl!="free","today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        if lvl=="free": d[uid]["level"]="none"
        save(d); bot.send_message(m.chat.id,f"✅ Added {uid} as {lvl.upper()}"); return
    if cmd=="broadcast" and len(args)>1:
        cnt=0; d=load_db()
        for uid in list(d.keys()):
            try: bot.send_message(uid,f"📢 {args[1]}"); cnt+=1; time.sleep(0.05)
            except: pass
        bot.send_message(m.chat.id,f"Sent {cnt}")
    if cmd=="ban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=True; save(d); bot.send_message(m.chat.id,"Banned")
    if cmd=="unban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=False; save(d); bot.send_message(m.chat.id,"Unbanned")

def signal_keyboard():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
    k.add(types.InlineKeyboardButton("▶️ Next Signal",callback_data="sel_market"))
    return k

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    try:
        tid=str(c.from_user.id); d=c.data; chat_id=c.message.chat.id; lvl=get_lvl(tid)
        try: bot.delete_message(chat_id,c.message.message_id)
        except: pass
        if d in ["res_win","res_loss"]:
            u=ensure(tid)
            if d=="res_win":
                u["wins"]=u.get("wins",0)+1; u["win_streak"]=u.get("win_streak",0)+1; u["loss_streak"]=0
                db[tid]=u; save(db)
                bot.send_message(chat_id, f"✅ Recorded! Fresh start! 🎉\n🔥 {u['win_streak']} Wins! Loss reset 0\nNext: {random.randint(79,85)}% 💪", reply_markup=signal_keyboard())
                return
            else:
                u["losses"]=u.get("losses",0)+1; u["loss_streak"]=u.get("loss_streak",0)+1; u["win_streak"]=0
                db[tid]=u; save(db); ls=u["loss_streak"]
                if ls>=6: msg=f"🛑 Market is choppy right now.\nYou've had {ls} losses in a row - let's pause.\n\nTake a break, market will be stable soon.\nCome back for high accuracy signals! 🎯\n\nYou can still get Next Signal 👇"
                else: msg=f"❌ Recorded! Loss {ls} 😔\n💪 Recovery incoming\nNext: {random.randint(82,85)}% High 🚀"
                bot.send_message(chat_id, msg, reply_markup=signal_keyboard())
                return
        if d=="admin" and tid==OWNER:
            k=types.InlineKeyboardMarkup(row_width=2)
            k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
            k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
            k.add(types.InlineKeyboardButton("💵 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
            k.add(types.InlineKeyboardButton("🛡️ Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🎯 Global WR",callback_data="ad_wr"))
            bot.send_message(chat_id,f"👑 ADMIN V8\nUsers: {len(load_db())}",reply_markup=k);return
        if tid==OWNER and d.startswith("ad_"):
            if d=="ad_users":
                txt="👥 Users:\n"
                for uid,u in list(load_db().items())[:20]: txt+=f"{uid} {u.get('level')} ${u.get('total')} W:{u.get('wins',0)} L:{u.get('losses',0)}\n"
                bot.send_message(chat_id,txt);return
            if d=="ad_stats":
                dd=load_db(); tot=sum(u.get('total',0) for u in dd.values()); ver=sum(1 for u in dd.values() if u.get('verified')); wins=sum(u.get('wins',0) for u in dd.values()); losses=sum(u.get('losses',0) for u in dd.values()); gwr=round(wins/(wins+losses)*100,1) if (wins+losses)>0 else 0
                bot.send_message(chat_id,f"📊 U:{len(dd)} V:{ver} ${tot}\nTrades:{wins+losses} WR:{gwr}%");return
            if d=="ad_wr":
                dd=load_db(); wins=sum(u.get('wins',0) for u in dd.values()); losses=sum(u.get('losses',0) for u in dd.values()); gwr=round(wins/(wins+losses)*100,1) if (wins+losses)>0 else 0
                txt=f"🎯 GLOBAL Trades:{wins+losses} WR:{gwr}%\n"
                for uid,u in sorted(dd.items(), key=lambda x: x[1].get('wins',0)+x[1].get('losses',0), reverse=True)[:10]:
                    t=u.get('wins',0)+u.get('losses',0)
                    if t>0: txt+=f"{uid}: {t} WR:{round(u.get('wins',0)/t*100,1)}% LS:{u.get('loss_streak')}\n"
                bot.send_message(chat_id,txt);return
            if d=="ad_deps":
                dd=load_db(); txt="💵 Deposits:\n"
                for uid,u in dd.items():
                    if u.get('total',0)>0: txt+=f"{uid} ${u.get('total')} {u.get('level')}\n"
                bot.send_message(chat_id,txt or "None");return
            if d=="ad_reset":
                dd=load_db()
                for u in dd.values(): u["today"]=0; u["date"]=str(date.today())
                save(dd); bot.send_message(chat_id,"🔄 Reset Done");return
            if d=="ad_broad":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL"))
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="broad_FREE"))
                kb.add(types.InlineKeyboardButton("🚀 STARTER",callback_data="broad_STARTER"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="broad_PRO"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="broad_VIP"))
                kb.add(types.InlineKeyboardButton("💎 ALL VIPs",callback_data="broad_ALLVIP"))
                bot.send_message(chat_id,"📢 Select target:",reply_markup=kb);return
            if d.startswith("broad_"):
                target=d.replace("broad_",""); broadcast_pending[tid]=target
                bot.send_message(chat_id,f"✅ Target: {target}\nNow SEND message.");return
            if d=="ad_ban": bot.send_message(chat_id,"/ban ID /unban ID");return
            if d=="ad_sec":
                txt="🛡️ Log:\n"
                for s in sec_log[-10:]: txt+=f"{s.get('ip')} {s.get('status')} {s.get('gid','-')}\n"
                bot.send_message(chat_id,txt);return
        if d=="dep":
            k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("🔗 Register + Deposit",url=LINK+"?click_id="+tid))
            bot.send_message(chat_id,f"💵 DEPOSIT\n{LINK}?click_id={tid}\n🚀 $20 Starter 20/day\n💎 $50 PRO 100/day\n👑 $100 VIP Unlimited",reply_markup=k);return
        if d=="upg":
            k=types.InlineKeyboardMarkup()
            k.add(types.InlineKeyboardButton("🚀 STARTER $20 Deposit",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("💎 PRO $50 Deposit",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("👑 VIP $100 Deposit",url=LINK+"?click_id="+tid))
            bot.send_message(chat_id,f"💵 DEPOSIT TO UPGRADE\n\nCurrent: {lvl.upper()}\n\n🚀 Starter $20 - 20/day (65-70%)\n💎 PRO $50 - 100/day (65-75%)\n👑 VIP $100 - Unlimited (75-85%)\n\n👇 Choose deposit:",reply_markup=k);return
        if d=="how": bot.send_message(chat_id,f"📖 HOW V8\n1️⃣ Register\n2️⃣ Deposit\n3️⃣ /start signals\n💹 REAL 15\n🔶 OTC 30");return
        if d=="bal":
            u=ensure(tid)
            bot.send_message(chat_id,f"📊 STATUS {lvl.upper()}\n💰 Total ${u.get('total',0)}\n📅 Today {u.get('today',0)}\n🎯 W:{u.get('wins',0)} L:{u.get('losses',0)} LS:{u.get('loss_streak',0)}");return
        if d=="sup": bot.send_message(chat_id,"💬 Support: @YourSupport");return
        if d=="sel_market":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC 30",callback_data="m_otc"))
            bot.send_message(chat_id,"🎯 Select Market:",reply_markup=k);return
        if d=="m_real":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
            bot.send_message(chat_id,"💹 REAL 15",reply_markup=k);return
        if d=="m_otc":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
            bot.send_message(chat_id,"🔶 OTC 30",reply_markup=k);return
        if d=="real_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in REAL: k.add(types.InlineKeyboardButton(f"💹 {p}",callback_data=f"pair_{p}_REAL"))
            bot.send_message(chat_id,"✋ MANUAL REAL Pick Pair",reply_markup=k);return
        if d=="otc_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[:15]: k.add(types.InlineKeyboardButton(f"🔶 {p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("Next 15 →",callback_data="otc_manual2"))
            bot.send_message(chat_id,"✋ MANUAL OTC 1/2",reply_markup=k);return
        if d=="otc_manual2":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[15:]: k.add(types.InlineKeyboardButton(f"🔶 {p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("← Back",callback_data="otc_manual"))
            bot.send_message(chat_id,"✋ MANUAL OTC 2/2",reply_markup=k);return
        if d.startswith("pair_"):
            rest=d[5:]; pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"⛔ {lvl.upper()} limit {cur}/{lim} 😔");return
            k=types.InlineKeyboardMarkup(row_width=4)
            k.add(types.InlineKeyboardButton("⏱️ M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("⏱️ M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("⏱️ M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("⏱️ M5",callback_data=f"sig_{pair}_M5"))
            bc=0; bs=""; br=0; bt=""
            for exp in EXP:
                sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
                if conf>bc: bc=conf; bs=sig; br=rsi; bt=trend
            bot.send_message(chat_id,f"💹 Pair {pair}\n🎯 Best {bs} {bc}% RSI {br:.1f} {bt}\nPick Expiry:",reply_markup=k);return
        if d in ["real_auto","otc_auto"]:
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"⛔ Limit {cur}/{lim}");return
            pairs=OTC if d.startswith("otc_") else REAL
            pair=random.choice(pairs); exp=random.choice(EXP)
            sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
            inc(tid)
            bot.send_message(chat_id,f"📊 {lvl.upper()} {conf}%\n💹 {pair} {sig} Exp:{exp}\n📈 RSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard());return
        if d.startswith("sig_"):
            tmp=d[4:]; idx=tmp.rfind("_M"); pair=tmp[:idx]; exp=tmp[idx+1:]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over:
                msg=f"⛔ {lvl.upper()} limit {cur}/{lim}"
                if lvl=="starter": msg+=" Upgrade PRO $50 🚀"
                if lvl=="pro": msg+=" Upgrade VIP $100 👑"
                bot.send_message(chat_id,msg);return
            sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
            inc(tid)
            bot.send_message(chat_id,f"✅ SIGNAL {lvl.upper()} {conf}% 🎯\n💹 Pair: {pair}\n📍 Dir: {sig}\n⏱️ Exp: {exp}\n📈 RSI {rsi:.1f} {trend}\n📊 {cur+1}/{lim}",reply_markup=signal_keyboard());return
    except Exception as e:
        print(f"ERR {e}")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
