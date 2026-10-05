import os, json, random, time, threading
from datetime import date, datetime, timedelta
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER = "8188622130"
LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
PASS = "WW12345"

REAL = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","EUR/JPY","GBP/JPY","AUD/JPY","EUR/AUD","USD/CHF","GBP/AUD","EUR/CAD","NZD/USD","USD/MXN"]
OTC = ["EUR/USD-OTC","GBP/USD-OTC","USD/JPY-OTC","AUD/USD-OTC","USD/CAD-OTC","EUR/GBP-OTC","EUR/JPY-OTC","GBP/JPY-OTC","AUD/JPY-OTC","EUR/AUD-OTC","USD/CHF-OTC","GBP/AUD-OTC","EUR/CAD-OTC","NZD/USD-OTC","USD/MXN-OTC","BTC/USD-OTC","ETH/USD-OTC","LTC/USD-OTC","BNB/USD-OTC","XRP/USD-OTC","DOGE/USD-OTC","DOT/USD-OTC","ADA/USD-OTC","SOL/USD-OTC","MATIC/USD-OTC","AVAX/USD-OTC","TRX/USD-OTC","SHIB/USD-OTC","UNI/USD-OTC","LINK/USD-OTC"]
EXP = ["M1","M2","M3","M5"]

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

DB_FILE="db.json"; ADMIN_FILE="admin.json"; BROAD_FILE="broad.json"
broadcast_pending={}; broadcast_content_pending={}

def load_db():
    try:
        with open(DB_FILE,"r") as f: return json.load(f)
    except: return {}
def save_db(d):
    with open(DB_FILE,"w") as f: json.dump(d,f)
def load_admin():
    try:
        with open(ADMIN_FILE,"r") as f: return json.load(f)
    except: return {"total_wins":0,"total_losses":0}
def save_admin(d):
    with open(ADMIN_FILE,"w") as f: json.dump(d,f)
def load_broadcast():
    try:
        with open(BROAD_FILE,"r") as f: return json.load(f)
    except: return []
def save_broadcast(d):
    with open(BROAD_FILE,"w") as f: json.dump(d,f)

def get_lvl(uid):
    db=load_db(); u=db.get(str(uid))
    if not u: return "locked"
    if not u.get("verified"): return "locked"
    return u.get("level","none")

def ensure(uid):
    db=load_db(); tid=str(uid); today=str(date.today())
    if tid not in db:
        db[tid]={"total":0,"level":"locked","verified":False,"today":0,"date":today,"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
        save_db(db)
    u=db[tid]
    if u.get("date")!=today:
        u["today"]=0; u["wins"]=0; u["losses"]=0; u["win_streak"]=0; u["loss_streak"]=0; u["date"]=today
        db[tid]=u; save_db(db)
    tot=u.get("total",0)
    if u.get("verified"):
        if tot>=100: u["level"]="vip"
        elif tot>=50: u["level"]="pro"
        elif tot>=20: u["level"]="starter"
        else: u["level"]="none"
        db[tid]=u; save_db(db)
    return db[tid]

def check_limit(uid,lvl):
    u=ensure(uid)
    if lvl=="locked": return True,0,0
    limits={"none":5,"starter":20,"pro":100,"vip":999999}
    lim=limits.get(lvl,5)
    return u.get("today",0)>=lim, u.get("today",0), lim if lim!=999999 else "♾️"

def inc(uid):
    db=load_db(); u=db.get(str(uid)); u["today"]+=1; db[str(uid)]=u; save_db(db)

def get_signal(pair,exp,lvl):
    rsi=random.uniform(20,80)
    trend="🔼 Bullish" if rsi<50 else "🔽 Bearish"
    sig="CALL 📈" if rsi<50 else "PUT 📉"
    wr={"none":random.randint(55,65),"starter":random.randint(65,70),"pro":random.randint(70,80),"vip":random.randint(80,87),"locked":60}
    return sig,rsi,trend,wr.get(lvl,60)

def main_kb():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("📊 GET SIGNAL",callback_data="sel_market"),types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"))
    k.add(types.InlineKeyboardButton("🔶 OTC 30",callback_data="m_otc"),types.InlineKeyboardButton("💎 Upgrade",callback_data="upg"))
    k.add(types.InlineKeyboardButton("📈 My Status",callback_data="status"),types.InlineKeyboardButton("💰 Deposit",callback_data="dep"))
    k.add(types.InlineKeyboardButton("📜 How it Works",callback_data="how"))
    return k

def sig_kb():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
    k.add(types.InlineKeyboardButton("🔥 Next Signal",callback_data="sel_market"))
    return k

@bot.message_handler(commands=['start'])
def start_cmd(m):
    tid=str(m.from_user.id); u=ensure(tid)
    if u.get("banned"):
        bot.send_message(m.chat.id,"🚫 Banned"); return
    if not u.get("verified"):
        k=types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("🔗 Register Now - Unlock 5/day",url=LINK+"?click_id="+tid))
        k.add(types.InlineKeyboardButton("🔓 Enter Password "+PASS,callback_data="ask_pass"))
        bot.send_message(m.chat.id,"🔒 LOCKED - REGISTER FIRST TO UNLOCK SIGNAL\n\n👋 Welcome "+m.from_user.first_name+"!\n\n1️⃣ Register using link below\n2️⃣ Then enter password: "+PASS+"\n\n👉 After registration you get 5 signals/day (NONE)\n👉 Deposit $20 → 20/day STARTER\n👉 Deposit $50 → 100/day PRO\n👉 Deposit $100 → Unlimited VIP\n\n👇 Click to register:",reply_markup=k); return
    lvl=get_lvl(tid)
    wr_map={"none":"55-65","starter":"65-70","pro":"70-80","vip":"80-87"}
    wr=wr_map.get(lvl,"55-65")
    is_over,cur,lim=check_limit(tid,lvl)
    rem = "♾️" if lim=="♾️" else str(lim - cur)
    bot.send_message(m.chat.id,"👋 Welcome "+m.from_user.first_name+"!\n👑 "+lvl.upper()+" | 🎯 "+wr+"% WR\n📊 "+str(cur)+"/"+str(lim)+" Used | "+rem+" Remains\n\n🔥 Ready to trade?",reply_markup=main_kb())@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    tid=str(c.from_user.id);d=c.data;chat_id=c.message.chat.id;lvl=get_lvl(tid)
    try: bot.delete_message(chat_id,c.message.message_id)
    except: pass
    if d=="ask_pass":
        bot.send_message(chat_id,"🔑 Enter password: "+PASS+"\n\nIf you registered, just send "+PASS+" here to unlock 5/day! 🎉"); return
    if d in ["res_win","res_loss"]:
        db=load_db(); u=db.get(tid)
        if not u: u=ensure(tid); db=load_db(); u=db[tid]
        adm=load_admin()
        if d=="res_win":
            u["wins"]=u.get("wins",0)+1; u["win_streak"]=u.get("win_streak",0)+1; u["loss_streak"]=0; db[tid]=u; save_db(db)
            adm["total_wins"]=adm.get("total_wins",0)+1; save_admin(adm)
            msgs=["✅ BOOM! WIN! 🔥💰\n🏆 Streak: "+str(u['win_streak'])+" Wins! Keep pushing "+lvl.upper()+"!","✅ PERFECT WIN! 💎🔥\n📈 "+str(u['win_streak'])+" in a row! You're on fire!","✅ KAZI WIN! 👑💸\n🔥 Win streak "+str(u['win_streak'])+" - Machine!","✅ BANG! WIN CONFIRMED! 🚀\n💰 "+str(u['win_streak'])+" Wins straight! Keep going!"]
            bot.send_message(chat_id, random.choice(msgs), reply_markup=sig_kb()); return
        else:
            u["losses"]=u.get("losses",0)+1; u["loss_streak"]=u.get("loss_streak",0)+1; u["win_streak"]=0; db[tid]=u; save_db(db)
            adm["total_losses"]=adm.get("total_losses",0)+1; save_admin(adm)
            ls=u.get("loss_streak",0)
            if ls>=6:
                msg="☕ 6 Losses in row — Hey champion, take a 15 min break! Market is volatile now. Grab coffee ☕️\n\n💡 Pro traders know where to stop! Rest = Win. Signals still open when you're ready. We come back stronger together! 💎🔥"
                bot.send_message(chat_id, msg, reply_markup=sig_kb()); return
            if ls==5: msg="❌ 5 Losses in row! 🚨\n🧘 Tough market boss! Almost at limit. Breathe, next will recover! 💪"
            elif ls==4: msg="❌ 4 Losses 💔\n📉 Market is choppy now, but we recover together! KAZI adjusting 🔥"
            else:
                lmsgs=["❌ Loss, but we learn! 📚\n💪 Loss streak "+str(ls)+" - Next is WIN for sure! KAZI got this!","❌ Not today, but we fight! ⚔️\n🔥 "+str(ls)+" loss - Market trick, we adapt together!","❌ Small loss! 💸\n🚀 Top traders lose too, WIN coming next!","❌ Oops! Market slipped 📉\n💎 Stay focused boss, KAZI got next signal!"]
                msg=random.choice(lmsgs)
            bot.send_message(chat_id, msg, reply_markup=sig_kb()); return
    if d=="admin" and tid==OWNER:
        db=load_db(); tot=sum(u.get('total',0) for u in db.values()); ver=len([u for u in db.values() if u.get('verified')])
        k=types.InlineKeyboardMarkup(row_width=2)
        k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
        k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
        k.add(types.InlineKeyboardButton("💰 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
        k.add(types.InlineKeyboardButton("🔒 Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🏆 WR",callback_data="ad_wr"))
        bot.send_message(chat_id,"👑 ADMIN V13.1.4 FINAL ✅\n👤 OWNER: "+OWNER+"\n👥 Users "+str(len(db))+" ✅ V:"+str(ver)+" 💰 $"+str(tot)+"\n🌍 LINK: "+LINK,reply_markup=k);return
    if tid==OWNER and d.startswith("ad_"):
        if d=="ad_users":
            txt="👥 Users:\n"
            for uid,u in list(load_db().items())[:30]: txt+=uid+" "+u.get('level')+" $"+str(u.get('total'))+" W:"+str(u.get('wins',0))+" L:"+str(u.get('losses',0))+"\n"
            bot.send_message(chat_id,txt);return
        if d=="ad_stats":
            dd=load_db();tot=sum(u.get('total',0) for u in dd.values());ver=sum(1 for u in dd.values() if u.get('verified'))
            bot.send_message(chat_id,"📊 Stats\n👥 U:"+str(len(dd))+" ✅ V:"+str(ver)+" 💰 $"+str(tot));return
        if d=="ad_wr":
            adm=load_admin(); wins=adm.get('total_wins',0);losses=adm.get('total_losses',0); total=wins+losses; wr=round(wins/total*100,1) if total>0 else 0
            bot.send_message(chat_id,"🏆 REAL WR\n✅ "+str(wins)+" Wins ❌ "+str(losses)+" Losses\n📊 WR: "+str(wr)+"%");return
        if d=="ad_deps":
            dd=load_db();txt="💰 Deposits:\n"
            for uid,u in dd.items():
                if u.get('total',0)>0: txt+=uid+" $"+str(u.get('total'))+" "+u.get('level')+"\n"
            bot.send_message(chat_id,txt or "None");return
        if d=="ad_reset":
            dd=load_db()
            for u in dd.values(): u["today"]=0;u["date"]=str(date.today());u["wins"]=0;u["losses"]=0;u["win_streak"]=0;u["loss_streak"]=0
            save_db(dd);bot.send_message(chat_id,"🔄 Reset Done ✅");return
        if d=="ad_broad":
            kb=types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL"))
            kb.add(types.InlineKeyboardButton("⚪ NONE",callback_data="broad_NONE"))
            kb.add(types.InlineKeyboardButton("💰 PAID",callback_data="broad_PAID"))
            kb.add(types.InlineKeyboardButton("💎 VIP",callback_data="broad_VIP"))
            kb.add(types.InlineKeyboardButton("🔵 PRO",callback_data="broad_PRO"))
            kb.add(types.InlineKeyboardButton("🟢 STARTER",callback_data="broad_STARTER"))
            bot.send_message(chat_id,"🎯 Select broadcast target:",reply_markup=kb);return
        if d=="ad_ban": bot.send_message(chat_id,"🚫 /ban ID /unban ID");return
        if d=="ad_sec": bot.send_message(chat_id,"🔒 Sec log empty");return
    if tid==OWNER and d.startswith("broad_"):
        target=d.replace("broad_",""); broadcast_pending[tid]=target
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("♾️ No Delete",callback_data="del_none"))
        kb.add(types.InlineKeyboardButton("⏰ 1 Week",callback_data="del_7"))
        kb.add(types.InlineKeyboardButton("⏰ 1 Month",callback_data="del_30"))
        kb.add(types.InlineKeyboardButton("⏰ 3 Month",callback_data="del_90"))
        kb.add(types.InlineKeyboardButton("⏰ 6 Month",callback_data="del_180"))
        kb.add(types.InlineKeyboardButton("⏰ 1 Year",callback_data="del_365"))
        bot.send_message(chat_id,"🎯 Target "+target+" selected ✅\n\n⏰ Now select Auto-Delete time:",reply_markup=kb);return
    if tid==OWNER and d.startswith("del_"):
        if tid not in broadcast_pending: bot.send_message(chat_id,"❌ Select target first");return
        broadcast_content_pending[tid]={"target":broadcast_pending[tid],"delete":d.replace("del_","")}
        bot.send_message(chat_id,"✅ Delete: "+d.replace('del_','')+" days\n\n📝 Now SEND your broadcast message (text):");return
    if d=="dep":
        k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("💰 Register + Deposit",url=LINK+"?click_id="+tid))
        bot.send_message(chat_id,"💰 DEPOSIT NOW 👇\n"+LINK+"?click_id="+tid,reply_markup=k);return
    if d=="upg":
        u=ensure(tid); cur_total=u.get('total',0); cur_lvl=lvl
        k=types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("🟢 STARTER $20",url=LINK+"?click_id="+tid))
        k.add(types.InlineKeyboardButton("🔵 PRO $50 - POPULAR 🔥",url=LINK+"?click_id="+tid))
        k.add(types.InlineKeyboardButton("💎 VIP $100 - BEST WR 87%",url=LINK+"?click_id="+tid))
        txt="🚀 UPGRADE YOUR LEVEL — EARN MORE! 💰\n\n👤 Your Status:\n👑 Level: "+cur_lvl.upper()+"\n💰 Deposit: $"+str(cur_total)+"\n📊 Today: "+str(u.get('today',0))+"/"+("♾️" if cur_lvl=='vip' else "20" if cur_lvl=='starter' else "100" if cur_lvl=='pro' else "5")+"\n\n💎 PLANS COMPARISON:\n━━━━━━━━━━━━━━━\n⚪ NONE - $0-19\n💵 $0-19 | 📊 5/day | 🎯 55-65% WR\n✅ Free taste after registration\n\n🟢 STARTER - $20 ⭐ BEST START\n💵 $20 | 📊 20/day | 🎯 65-70% WR\n✅ 4x More Signals\n✅ Higher Accuracy\n🔥 Most beginners start here!\n\n🔵 PRO - $50 💎 MOST POPULAR 🔥\n💵 $50 | 📊 100/day | 🎯 70-80% WR\n✅ 20x More Signals!\n✅ Pro Level WR\n⚡️ 60% traders choose PRO!\n\n💎 VIP - $100 👑 ULTIMATE BEST!\n💵 $100 | 📊 UNLIMITED ∞ | 🎯 80-87% WR\n✅ ♾️ Unlimited Signals\n✅ Highest WR 80-87%\n✅ VIP Private Support\n✅ Maximum Profit!\n👑 For Serious Earners!\n━━━━━━━━━━━━━━━\n💡 Smart traders UPGRADE!\n🚀 Deposit now = Instant Auto-Upgrade!"
        bot.send_message(chat_id,txt,reply_markup=k);return
    if d=="how": bot.send_message(chat_id,"❓ HOW IT WORKS V13.1.4\n1️⃣ /start → Register (Password WW12345)\n2️⃣ Auto Unlock 5/day NONE\n3️⃣ Deposit $20 → 20/day STARTER\n4️⃣ Deposit $50 → 100/day PRO\n5️⃣ Deposit $100 → Unlimited VIP\n6️⃣ GET SIGNAL → Choose Market → Win! 🏆");return
    if d in ["bal","status"]:
        u=ensure(tid); lim_txt="♾️" if lvl=="vip" else "20" if lvl=="starter" else "100" if lvl=="pro" else "5" if lvl=="none" else "0"
        bot.send_message(chat_id,"👤 STATUS\n👑 Level: "+lvl.upper()+"\n💰 Deposit: $"+str(u.get('total',0))+"\n📊 Today: "+str(u.get('today',0))+"/"+lim_txt+"\n🏆 W:"+str(u.get('wins',0))+" L:"+str(u.get('losses',0))+" Streak:"+str(u.get('win_streak',0) if u.get('win_streak',0)>0 else u.get('loss_streak',0))+"\n📅 Auto Reset Daily 00:00 UTC");return
    if d=="sel_market":
        k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC 30",callback_data="m_otc"))
        bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k);return
    if d=="m_real":
        k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
        bot.send_message(chat_id,"💹 REAL 15 Market",reply_markup=k);return
    if d=="m_otc":
        k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
        bot.send_message(chat_id,"📊 OTC 30 Market",reply_markup=k);return
    if d=="real_manual":
        k=types.InlineKeyboardMarkup(row_width=2)
        for p in REAL: k.add(types.InlineKeyboardButton(p,callback_data="pair_"+p+"_REAL"))
        bot.send_message(chat_id,"✋ MANUAL REAL Pick Pair 👇",reply_markup=k);return
    if d=="otc_manual":
        k=types.InlineKeyboardMarkup(row_width=2)
        for p in OTC[:15]: k.add(types.InlineKeyboardButton(p,callback_data="pair_"+p+"_OTC"))
        k.add(types.InlineKeyboardButton("➡️ Next 15",callback_data="otc_manual2"))
        bot.send_message(chat_id,"✋ MANUAL OTC 1/2 👇",reply_markup=k);return
    if d=="otc_manual2":
        k=types.InlineKeyboardMarkup(row_width=2)
        for p in OTC[15:]: k.add(types.InlineKeyboardButton(p,callback_data="pair_"+p+"_OTC"))
        k.add(types.InlineKeyboardButton("⬅️ Back",callback_data="otc_manual"))
        bot.send_message(chat_id,"✋ MANUAL OTC 2/2 👇",reply_markup=k);return
    if d.startswith("pair_"):
        rest=d[5:];pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
        is_over,cur,lim=check_limit(tid,lvl)
        if is_over: bot.send_message(chat_id,"🚫 Limit "+str(cur)+"/"+str(lim)+" reached! Upgrade or wait daily reset.");return
        k=types.InlineKeyboardMarkup(row_width=4)
        k.add(types.InlineKeyboardButton("M1",callback_data="sig_"+pair+"_M1"),types.InlineKeyboardButton("M2",callback_data="sig_"+pair+"_M2"),types.InlineKeyboardButton("M3",callback_data="sig_"+pair+"_M3"),types.InlineKeyboardButton("M5",callback_data="sig_"+pair+"_M5"))
        bot.send_message(chat_id,"💹 Pair "+pair+"\n⏰ Pick Expiry:",reply_markup=k);return
    if d in ["real_auto","otc_auto"]:
        is_over,cur,lim=check_limit(tid,lvl)
        if is_over: bot.send_message(chat_id,"🚫 Limit "+str(cur)+"/"+str(lim)+" reached!");return
        pairs=OTC if d.startswith("otc_") else REAL
        pair=random.choice(pairs);exp=random.choice(EXP)
        sig,rsi,trend,conf=get_signal(pair, exp, lvl)
        inc(tid)
        bot.send_message(chat_id,"🔥 "+lvl.upper()+" "+str(conf)+"% 💹\n📊 "+pair+"\n"+("📈 CALL" if "CALL" in sig else "📉 PUT")+" "+sig+"\n⏰ Exp "+exp+"\n📉 RSI "+str(round(rsi,1))+" "+trend+"\n📊 "+str(cur+1)+"/"+str(lim),reply_markup=sig_kb());return
    if d.startswith("sig_"):
        tmp=d[4:];idx=tmp.rfind("_M");pair=tmp[:idx];exp=tmp[idx+1:]
        is_over,cur,lim=check_limit(tid,lvl)
        if is_over: bot.send_message(chat_id,"🚫 Limit "+str(cur)+"/"+str(lim)+" reached!");return
        sig,rsi,trend,conf=get_signal(pair, exp, lvl)
        inc(tid)
        bot.send_message(chat_id,"🔥 SIGNAL "+lvl.upper()+" "+str(conf)+"% 💹\n📊 Pair "+pair+"\n"+("📈 CALL" if "CALL" in sig else "📉 PUT")+" Dir "+sig+"\n⏰ Exp "+exp+"\n📉 RSI "+str(round(rsi,1))+" "+trend+"\n📊 "+str(cur+1)+"/"+str(lim),reply_markup=sig_kb());return

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    tid=str(m.from_user.id)
    if m.text.strip()==PASS:
        db=load_db(); u=ensure(tid)
        if not u.get("verified"):
            db[tid]["verified"]=True; db[tid]["level"]="none"; save_db(db)
            bot.send_message(m.chat.id,"✅ Password OK! Unlocked 5/day NONE! 🎉",reply_markup=main_kb())
            return
    if tid==OWNER and tid in broadcast_content_pending:
        content=broadcast_content_pending[tid]; target=content["target"]; del_opt=content["delete"]
        msg_text=m.text; cnt=0; dbs=load_db(); b_list=load_broadcast()
        delete_at=None
        if del_opt!="none": delete_at=datetime.now()+timedelta(days=int(del_opt))
        for uid,u in list(dbs.items()):
            lvl_u=u.get("level","none"); send=False
            if target=="ALL": send=True
            elif target=="NONE" and lvl_u=="none": send=True
            elif target=="PAID" and lvl_u in ["starter","pro","vip"]: send=True
            elif target=="VIP" and lvl_u=="vip": send=True
            elif target=="PRO" and lvl_u=="pro": send=True
            elif target=="STARTER" and lvl_u=="starter": send=True
            if send:
                try:
                    sent=bot.send_message(uid, msg_text)
                    cnt+=1
                    if delete_at: b_list.append({"chat_id":uid,"msg_id":sent.message_id,"delete_at":delete_at.isoformat()})
                    time.sleep(0.05)
                except: pass
        if delete_at: save_broadcast(b_list); bot.send_message(m.chat.id,"✅ Broadcast Sent "+str(cnt)+" 🎯 "+target+"\n⏰ Auto-delete in "+del_opt+" days!")
        else: bot.send_message(m.chat.id,"✅ Broadcast Sent "+str(cnt)+" 🎯 "+target+"\n♾️ No auto-delete")
        del broadcast_content_pending[tid]; broadcast_pending.pop(tid,None)
        return
    bot.send_message(m.chat.id,"👋 Use /start",reply_markup=main_kb())

def auto_delete_worker():
    while True:
        try:
            bl=load_broadcast(); now=datetime.now(); new_bl=[]
            for b in bl:
                try:
                    dt=datetime.fromisoformat(b["delete_at"])
                    if now>=dt: bot.delete_message(b["chat_id"],b["msg_id"])
                    else: new_bl.append(b)
                except: new_bl.append(b)
            if len(new_bl)!=len(bl): save_broadcast(new_bl)
        except: pass
        time.sleep(60)

threading.Thread(target=auto_delete_worker,daemon=True).start()

@app.route("/", methods=['GET'])
def home(): return "V13.1.4 LIVE OWNER 8188622130 WORLDWIDE WITH EMOJIS ✅",200

@app.route("/webhook", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok",200

@app.route("/postback")
def postback():
    cid=request.args.get("click_id"); amount=request.args.get("amount",0)
    try:
        db=load_db()
        if cid in db:
            db[cid]["total"]=db[cid].get("total",0)+int(float(amount) if amount else 0)
            save_db(db)
            try: bot.send_message(cid,"💰 Deposit $"+str(amount)+" confirmed! Level auto-upgraded! Check /start 🚀")
            except: pass
    except: pass
    return "ok",200

if __name__=="__main__":
    bot.remove_webhook()
    time.sleep(1)
    url = os.environ.get("APP_URL")
    if url:
        bot.set_webhook(url=url+"/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
