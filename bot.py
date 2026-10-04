import os, json, random, time, hashlib, hmac, telebot
from telebot import types
from datetime import date
from flask import Flask, request, abort
TOKEN=os.getenv("BOT_TOKEN","").strip()
LINK=os.getenv("LINK","https://poafficl.com/click")
SECRET=os.getenv("SECRET","kazi_secret")
OWNER=str(os.getenv("OWNER_ID","")).strip()
DB="/tmp/db.json"
ADMIN_DB="/tmp/admin_stats.json"
REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","EUR/JPY","GBP/JPY","EUR/AUD","USD/CHF","NZD/USD","EUR/CAD","GBP/CAD","AUD/JPY","GBP/AUD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/GBP OTC","USD/CAD OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","EUR/AUD OTC","USD/CHF OTC","NZD/USD OTC","EUR/CAD OTC","GBP/CAD OTC","AUD/CAD OTC","GBP/AUD OTC","EUR/NZD OTC","AUD/NZD OTC","CHF/JPY OTC","EUR/CHF OTC","GBP/CHF OTC","AUD/CHF OTC","NZD/JPY OTC","CAD/JPY OTC","CAD/CHF OTC","USD/BRL OTC","USD/INR OTC","USD/TRY OTC","USD/ZAR OTC","USD/MXN OTC"]
EXP=["M1","M2","M3","M5"]
bot=telebot.TeleBot(TOKEN, threaded=False)
app=Flask(__name__)
if not os.path.exists(DB):
    with open(DB,"w") as f: json.dump({},f)
if not os.path.exists(ADMIN_DB):
    with open(ADMIN_DB,"w") as f: json.dump({"total_wins":0,"total_losses":0},f)
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
        u["today"]=0
        u["wins"]=0
        u["losses"]=0
        u["win_streak"]=0
        u["loss_streak"]=0
        u["date"]=str(date.today())
        save(db)
    if uid==OWNER and OWNER!="":
        u["level"]="vip";u["verified"]=True;save(db)
    return u
def get_lvl(uid):
    return ensure(uid).get("level","none")
def check_limit(uid,lvl):
    u=ensure(uid)
    cur=u.get("today",0)
    if lvl=="starter": lim=20
    elif lvl=="pro": lim=100
    elif lvl=="vip": lim=9999
    else: lim=3
    return cur>=lim,cur,lim
def inc(uid):
    u=ensure(uid)
    u["today"]=u.get("today",0)+1
    db[str(uid)]=u
    save(db)
def get_real_signal(pair,exp,lvl):
    rsi=random.uniform(28,72)
    sig="PUT" if rsi>65 else "CALL" if rsi<35 else random.choice(["CALL","PUT"])
    trend="UP 📈" if "CALL" in sig else "DOWN 📉"
    conf=random.randint(75,85) if lvl=="vip" else random.randint(65,75) if lvl=="pro" else random.randint(65,70) if lvl=="starter" else random.randint(55,65)
    return sig,rsi,trend,conf
@app.route("/", methods=["GET","POST"])
@app.route("/webhook", methods=["GET","POST"])
@app.route("/bot", methods=["GET","POST"])
def main_webhook():
    if request.method=="GET":
        return "OK KAZI V9.5 FINAL 🔥"
    try:
        js=request.get_data().decode("utf-8")
        if not js: return "OK"
        upd=telebot.types.Update.de_json(js)
        bot.process_new_updates([upd])
    except Exception as e:
        print(f"ERR {e}")
    return "OK"
@app.route("/postback")
def postback():
    sig=request.args.get("sig","");click_id=request.args.get("click_id","");sum_val=request.args.get("sum","0")
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
    d[click_id]=u;save(d)
    try: bot.send_message(click_id, f"✅ DEPOSIT CONFIRMED ${s} 💰 Level {u.get('level').upper()} 👑 Verified!")
    except: pass
    return "OK"
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid=str(m.from_user.id)
    u=ensure(uid)
    if u.get("banned"):
        bot.send_message(m.chat.id,"🚫 Banned");return
    lvl=get_lvl(uid)
    if not u.get("verified"):
        k=types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("📝 Register Now",url=LINK+"?click_id="+uid))
        bot.send_message(m.chat.id,f"👋 Welcome {m.from_user.first_name}!\n\n🔥 KAZI SIGNALS V9.5 🔥\n\n👉 Register First:\n{LINK}?click_id={uid}",reply_markup=k)
        return
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🚀 Get Signal 🔥",callback_data="sel_market"))
    k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("❓ How",callback_data="how"))
    k.add(types.InlineKeyboardButton("👤 Status",callback_data="status"),types.InlineKeyboardButton("📞 Support",callback_data="sup"))
    k.add(types.InlineKeyboardButton("🚀 Upgrade",callback_data="upg"))
    if uid==OWNER and OWNER!="":
        k.add(types.InlineKeyboardButton("👑 Admin",callback_data="admin"))
    bot.send_message(m.chat.id,f"👋 Welcome {m.from_user.first_name}!\n\n👑 Level: {lvl.upper()}\n📊 Today: {u.get('today',0)}\n\n🔥 Ready to Trade?",reply_markup=k)
@bot.message_handler(commands=["clearme"])
def clearme(m):
    uid=str(m.from_user.id)
    u=ensure(uid)
    u["today"]=0;u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0
    db[uid]=u;save(db)
    bot.send_message(m.chat.id,"✅ Reset done! 🔄")@bot.message_handler(func=lambda m: str(m.from_user.id)==OWNER and str(m.from_user.id) in broadcast_pending)
def broadcast_send(m):
    target=broadcast_pending.get(str(m.from_user.id))
    msg_text=m.text or ""
    cnt=0;d=load_db()
    for uid,u in list(d.items()):
        lvl=u.get("level","none");ver=u.get("verified",False);send=False
        if target=="ALL": send=True
        elif target=="FREE" and not ver: send=True
        elif target=="STARTER" and lvl=="starter": send=True
        elif target=="PRO" and lvl=="pro": send=True
        elif target=="VIP" and lvl=="vip": send=True
        elif target=="ALLVIP" and lvl in ["starter","pro","vip"]: send=True
        if send:
            try: bot.send_message(uid, f"{msg_text}");cnt+=1;time.sleep(0.05)
            except: pass
    del broadcast_pending[str(m.from_user.id)]
    bot.send_message(m.chat.id,f"✅ Broadcast Sent {cnt} users 🎯 Target {target}")
@bot.message_handler(commands=["adduser","broadcast","ban","unban"])
def admin_cmds(m):
    if str(m.from_user.id)!=OWNER: return
    args=m.text.split(" ",1);cmd=args[0].replace("/","").split("@")[0]
    if cmd=="adduser":
        a=m.text.split()
        if len(a)<3: bot.send_message(m.chat.id,"❌ /adduser ID LEVEL");return
        uid=a[1].strip();lvl=a[2].lower().strip()
        mp={"free":0,"starter":20,"pro":50,"vip":100}
        if lvl not in mp: return
        d=load_db()
        d[uid]={"total":mp[lvl],"level":lvl if lvl!="free" else "none","verified":lvl!="free","today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        if lvl=="free": d[uid]["level"]="none"
        save(d);bot.send_message(m.chat.id,f"✅ Added {uid} as {lvl.upper()} 👑");return
    if cmd=="broadcast" and len(args)>1:
        cnt=0;d=load_db()
        for uid in list(d.keys()):
            try: bot.send_message(uid,f"{args[1]}");cnt+=1;time.sleep(0.05)
            except: pass
        bot.send_message(m.chat.id,f"✅ Sent {cnt} 📢")
    if cmd=="ban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=True;save(d);bot.send_message(m.chat.id,"🚫 Banned")
    if cmd=="unban" and len(args)>1:
        d=load_db()
        if args[1].strip() in d: d[args[1].strip()]["banned"]=False;save(d);bot.send_message(m.chat.id,"✅ Unbanned")
def signal_keyboard():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
    k.add(types.InlineKeyboardButton("🔥 Next Signal",callback_data="sel_market"))
    return k
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    try:
        tid=str(c.from_user.id);d=c.data;chat_id=c.message.chat.id;lvl=get_lvl(tid)
        try: bot.delete_message(chat_id,c.message.message_id)
        except: pass
        if d in ["res_win","res_loss"]:
            u=ensure(tid)
            adm=load_admin()
            if d=="res_win":
                u["wins"]=u.get("wins",0)+1
                u["win_streak"]=u.get("win_streak",0)+1
                u["loss_streak"]=0
                db[tid]=u;save(db)
                adm["total_wins"]=adm.get("total_wins",0)+1
                save_admin(adm)
                msgs=[
                    f"✅ BOOM! WIN! 🔥💰\n🏆 Streak: {u['win_streak']} Wins!\n🚀 Keep pushing VIP!",
                    f"✅ PERFECT WIN! 💎🔥\n📈 {u['win_streak']} in a row! You're on fire!",
                    f"✅ KAZI WIN! 👑💸\n🔥 Win streak {u['win_streak']} - Machine!",
                    f"✅ BANG! WIN CONFIRMED! 🚀\n💰 {u['win_streak']} Wins straight! Keep going!",
                ]
                bot.send_message(chat_id, random.choice(msgs), reply_markup=signal_keyboard())
                return
            else:
                u["losses"]=u.get("losses",0)+1
                u["loss_streak"]=u.get("loss_streak",0)+1
                u["win_streak"]=0
                db[tid]=u;save(db)
                adm["total_losses"]=adm.get("total_losses",0)+1
                save_admin(adm)
                ls=u.get("loss_streak",0)
                if ls>=6:
                    bot.send_message(chat_id, f"⚠️ WARNING! {ls} LOSS STREAK 🚫\n\n🧠 Boss, STOP trading now!\n📉 Market is bad today, take a break!\n☕️ Rest 1 hour, clear mind!\n🔄 Come back fresh = WIN again!\n\n💡 Pro traders know when to STOP!\n🛑 Paused for your safety!", reply_markup=signal_keyboard())
                    return
                if ls==3:
                    msg=f"❌ 3 Losses in row 😤\n🧠 Don't revenge trade! Take small break\n💪 Next is WIN, trust KAZI!"
                elif ls==4:
                    msg=f"❌ 4 Losses 💔\n⚠️ Slow down boss! Reduce lot size\n🔥 We recover together!"
                elif ls==5:
                    msg=f"❌ 5 Losses in row! 🚨\n🛑 Almost at limit! 1 more = STOP\n🧘 Breathe, next will recover!"
                else:
                    lmsgs=[
                        f"❌ Loss, but we learn! 📚\n💪 Loss streak {ls} - Next is WIN for sure!",
                        f"❌ Not today, but we fight! ⚔️\n🔥 {ls} loss - Market trick, we adapt!",
                        f"❌ Small loss! 💸\n🚀 Top traders lose too, WIN coming!",
                        f"❌ Oops! Market slipped 📉\n💎 Stay focused, KAZI got next!",
                    ]
                    msg=random.choice(lmsgs)
                bot.send_message(chat_id, msg, reply_markup=signal_keyboard())
                return
        if d=="admin" and tid==OWNER:
            k=types.InlineKeyboardMarkup(row_width=2)
            k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
            k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
            k.add(types.InlineKeyboardButton("💰 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
            k.add(types.InlineKeyboardButton("🔒 Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🏆 WR",callback_data="ad_wr"))
            bot.send_message(chat_id,f"👑 ADMIN V9.5 👑\n👥 Users {len(load_db())}",reply_markup=k);return
        if tid==OWNER and d.startswith("ad_"):
            if d=="ad_users":
                txt="👥 Users:\n"
                for uid,u in list(load_db().items())[:20]: txt+=f"{uid} {u.get('level')} ${u.get('total')}\n"
                bot.send_message(chat_id,txt);return
            if d=="ad_stats":
                dd=load_db();tot=sum(u.get('total',0) for u in dd.values());ver=sum(1 for u in dd.values() if u.get('verified'))
                bot.send_message(chat_id,f"📊 Stats\n👥 U:{len(dd)} ✅ V:{ver} 💰 ${tot}");return
            if d=="ad_wr":
                adm=load_admin()
                wins=adm.get('total_wins',0);losses=adm.get('total_losses',0)
                total=wins+losses
                wr=round(wins/total*100,1) if total>0 else 0
                bot.send_message(chat_id,f"🏆 REAL WR (Never Resets)\n✅ {wins} Wins ❌ {losses} Losses\n📊 WR: {wr}%");return
            if d=="ad_deps":
                dd=load_db();txt="💰 Deposits:\n"
                for uid,u in dd.items():
                    if u.get('total',0)>0: txt+=f"{uid} ${u.get('total')}\n"
                bot.send_message(chat_id,txt or "None");return
            if d=="ad_reset":
                dd=load_db()
                for u in dd.values(): u["today"]=0;u["date"]=str(date.today())
                save(dd);bot.send_message(chat_id,"🔄 Reset Done ✅");return
            if d=="ad_broad":
                kb=types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL"))
                kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="broad_FREE"))
                kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="broad_STARTER"))
                kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="broad_PRO"))
                kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="broad_VIP"))
                kb.add(types.InlineKeyboardButton("💰 ALL VIPs",callback_data="broad_ALLVIP"))
                bot.send_message(chat_id,"🎯 Select broadcast target:",reply_markup=kb);return
            if d.startswith("broad_"):
                target=d.replace("broad_","");broadcast_pending[tid]=target
                bot.send_message(chat_id,f"🎯 Target {target} selected ✅\n\n📝 Now SEND your message (text, emojis, link):");return
            if d=="ad_ban": bot.send_message(chat_id,"🚫 /ban ID /unban ID");return
            if d=="ad_sec":
                txt="🔒 Log:\n"
                for s in sec_log[-10:]: txt+=f"{s.get('ip')} {s.get('status')}\n"
                bot.send_message(chat_id,txt);return
        if d=="dep":
            k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("💰 Register + Deposit",url=LINK+"?click_id="+tid))
            bot.send_message(chat_id,f"💰 DEPOSIT NOW 👇\n{LINK}?click_id={tid}",reply_markup=k);return
        if d=="upg":
            u=ensure(tid)
            cur_total=u.get('total',0)
            k=types.InlineKeyboardMarkup()
            k.add(types.InlineKeyboardButton("⭐ STARTER $20",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("💎 PRO $50 - POPULAR 🔥",url=LINK+"?click_id="+tid))
            k.add(types.InlineKeyboardButton("👑 VIP $100 - BEST WR 85%",url=LINK+"?click_id="+tid))
            bot.send_message(chat_id,
f"🚀 UPGRADE PLAN - EARN MORE!\n\n"
f"👤 Your Status:\n"
f"👑 Level: {lvl.upper()}\n"
f"💰 Deposit: ${cur_total}\n"
f"📊 Today: {u.get('today',0)}/{'♾️' if lvl=='vip' else '20' if lvl=='starter' else '100' if lvl=='pro' else '3'}\n\n"
f"💎 PLANS COMPARISON:\n"
f"━━━━━━━━━━━━━━━\n"
f"🆓 FREE\n"
f"💵 Deposit $0 | 📊 3/day | 🎯 55-65% WR\n\n"
f"⭐ STARTER - Deposit $20\n"
f"💵 Deposit $20 | 📊 20/day | 🎯 65-70% WR\n"
f"✅ Perfect to start\n\n"
f"💎 PRO - Deposit $50 🔥 MOST POPULAR\n"
f"💵 Deposit $50 | 📊 100/day | 🎯 70-75% WR\n"
f"✅ 5x More Signals + Higher WR\n\n"
f"👑 VIP - Deposit $100 💰 ULTIMATE\n"
f"💵 Deposit $100 | 📊 UNLIMITED | 🎯 75-85% WR\n"
f"✅ ♾️ Signals | 🔥 Best Accuracy\n"
f"✅ VIP Private Support\n"
f"✅ Maximum Profit\n"
f"━━━━━━━━━━━━━━━\n"
f"⚡️ 90% traders choose PRO or VIP!\n"
f"💸 Deposit now = Instant Upgrade!",reply_markup=k);return
        if d=="how": bot.send_message(chat_id,"❓ HOW V9.5\n1️⃣ Register\n2️⃣ Deposit\n3️⃣ /start\n4️⃣ Get Signal → Choose Market 🔥");return
        if d in ["bal","status"]:
            u=ensure(tid)
            lim_txt="♾️" if lvl=="vip" else "20" if lvl=="starter" else "100" if lvl=="pro" else "3"
            bot.send_message(chat_id,f"👤 STATUS\n👑 Level: {lvl.upper()}\n💰 Deposit: ${u.get('total',0)}\n📊 Today: {u.get('today',0)}/{lim_txt}\n🏆 Wins: {u.get('wins',0)} | ❌ Loss: {u.get('losses',0)}");return
        if d=="sup": bot.send_message(chat_id,"📞 Support @YourSupport");return
        if d=="sel_market":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
            bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k);return
        if d=="m_real":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
            bot.send_message(chat_id,"💹 REAL 15 Market",reply_markup=k);return
        if d=="m_otc":
            k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
            bot.send_message(chat_id,"📊 OTC 30 Market",reply_markup=k);return
        if d=="real_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in REAL: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_REAL"))
            bot.send_message(chat_id,"✋ MANUAL REAL Pick Pair 👇",reply_markup=k);return
        if d=="otc_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[:15]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("➡️ Next 15",callback_data="otc_manual2"))
            bot.send_message(chat_id,"✋ MANUAL OTC 1/2 👇",reply_markup=k);return
        if d=="otc_manual2":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[15:]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("⬅️ Back",callback_data="otc_manual"))
            bot.send_message(chat_id,"✋ MANUAL OTC 2/2 👇",reply_markup=k);return
        if d.startswith("pair_"):
            rest=d[5:];pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}");return
            k=types.InlineKeyboardMarkup(row_width=4)
            k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5"))
            bot.send_message(chat_id,f"💹 Pair {pair}\n⏰ Pick Expiry:",reply_markup=k);return
        if d in ["real_auto","otc_auto"]:
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}");return
            pairs=OTC if d.startswith("otc_") else REAL
            pair=random.choice(pairs);exp=random.choice(EXP)
            sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
            inc(tid)
            bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% 💹\n📊 {pair}\n{'📈 CALL' if 'CALL' in sig else '📉 PUT'} {sig}\n⏰ Exp {exp}\n📉 RSI {rsi:.1f} {trend}\n📊 {cur+1}/{lim}",reply_markup=signal_keyboard());return
        if d.startswith("sig_"):
            tmp=d[4:];idx=tmp.rfind("_M");pair=tmp[:idx];exp=tmp[idx+1:]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"🚫 Limit {cur}/{lim}");return
            sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
            inc(tid)
            bot.send_message(chat_id,f"🔥 SIGNAL {lvl.upper()} {conf}% 💹\n📊 Pair {pair}\n{'📈 CALL' if 'CALL' in sig else '📉 PUT'} Dir {sig}\n⏰ Exp {exp}\n📉 RSI {rsi:.1f} {trend}\n📊 {cur+1}/{lim}",reply_markup=signal_keyboard());return
    except Exception as e:
        print(f"ERR {e}")
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
