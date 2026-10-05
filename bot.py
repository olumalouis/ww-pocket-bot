import os, json, random, time, threading
from datetime import date
from flask import Flask, request
import telebot
from telebot import types
TOKEN=os.getenv("TOKEN") or os.getenv("BOT_TOKEN") or ""
OWNER="8188622130"
LINK=os.getenv("LINK","https://pocket-broker.com")
bot=telebot.TeleBot(TOKEN,threaded=False)
app=Flask(__name__)
REAL=["EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD","EURGBP","EURJPY","GBPJPY","AUDJPY","EURCAD","EURAUD","GBPCHF","EURCHF","NZDUSD","USDCHF"]
OTC=["EURUSD_OTC","GBPUSD_OTC","USDJPY_OTC","AUDUSD_OTC","USDCAD_OTC","EURGBP_OTC","EURJPY_OTC","GBPJPY_OTC","AUDJPY_OTC","NZDUSD_OTC","EURCHF_OTC","GBPCHF_OTC","CHFJPY_OTC","EURCAD_OTC","AUDCAD_OTC","CADJPY_OTC","GBPAUD_OTC","EURAUD_OTC","AUDCHF_OTC","NZDJPY_OTC","AUDNZD_OTC","EURCAD_OTC2","GBPCHF_OTC2","EURCHF_OTC2","AUDCAD_OTC2","EURNZD_OTC","GBPNZD_OTC","GBPCAD_OTC","EURGBP_OTC2","USDCHF_OTC"]
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
def ensure(uid):
    d=load_db()
    if uid not in d:
        if str(uid)==OWNER: d[uid]={"total":100,"level":"vip","verified":True,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0,"expires_at":"lifetime"}
        else: d[uid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
        save(d)
    return d[uid]
def get_lvl(uid):
    d=load_db(); u=d.get(uid)
    if not u: return "vip" if str(uid)==OWNER else "none"
    lvl=u.get("level","none")
    if str(uid)==OWNER and lvl=="none": return "vip"
    return lvl
def check_limit(uid,lvl):
    d=load_db(); u=d.get(uid,{})
    today=str(date.today())
    if u.get("date")!=today: u["today"]=0; u["wins"]=0; u["losses"]=0; u["win_streak"]=0; u["loss_streak"]=0; u["today_wins"]=0; u["today_losses"]=0; u["date"]=today; d[uid]=u; save(d)
    cur=u.get("today",0)
    if lvl=="vip": return False,cur,9999
    if lvl=="starter": lim=20
    elif lvl=="pro": lim=100
    else: lim=5
    return cur>=lim,cur,lim
def inc(uid):
    d=load_db(); u=d.get(uid)
    if u:
        if u.get("date")!=str(date.today()): u["today"]=0; u["date"]=str(date.today())
        u["today"]=u.get("today",0)+1; d[uid]=u; save(d)
def get_sig(pair,exp,lvl):
    if lvl=="vip": conf=random.randint(80,87)
    elif lvl=="pro": conf=random.randint(70,85)
    elif lvl=="starter": conf=random.randint(60,70)
    else: conf=random.randint(55,65)
    sig="BUY" if random.random()>0.5 else "SELL"
    rsi=random.uniform(25,75); trend="Up" if "BUY" in sig else "Down"
    return sig,rsi,trend,conf
def store_and_cleanup(chat_id,msg_id):
    if chat_id not in msg_hist: msg_hist[chat_id]=[]
    msg_hist[chat_id].append(msg_id)
    def do_cleanup():
        time.sleep(1.2)
        if chat_id in msg_hist and len(msg_hist[chat_id])>1:
            for old_id in msg_hist[chat_id][:-1]:
                try: bot.delete_message(chat_id,old_id)
                except: pass
            msg_hist[chat_id]=msg_hist[chat_id][-1:]
    threading.Thread(target=do_cleanup,daemon=True).start()
def get_main_kb(uid):
    k=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    k.add(types.KeyboardButton("🚀 Get Signal 🔥"))
    k.add(types.KeyboardButton("💰 Deposit"),types.KeyboardButton("❓ How"))
    k.add(types.KeyboardButton("👤 Status"),types.KeyboardButton("📞 Support"))
    k.add(types.KeyboardButton("🚀 Upgrade"))
    if str(uid)==OWNER: k.add(types.KeyboardButton("👑 Admin"))
    return k
def signal_keyboard():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
    k.add(types.InlineKeyboardButton("🔥 Next Signal",callback_data="sel_market"))
    return k
def is_owner_pending(m):
    if str(m.from_user.id)!=OWNER: return False
    tid=str(m.from_user.id)
    if tid in broadcast_data or tid in add_pending:
        if m.text and m.text.startswith("/"): return False
        return True
    return False
@app.route('/')
def home(): return "V12.6.5 NEW MOTIVATIONAL WARNINGS"
@app.route('/postback')
def pocket_postback():
    try:
        uid=request.args.get('click_id') or "0"
        amount=request.args.get('amount') or "0"
        try: amt=float(str(amount).replace('$','').replace(',','').strip())
        except: amt=0
        if amt<=0: return "Ignored",200
        d=load_db()
        if str(uid) not in d: d[str(uid)]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
        u=d[str(uid)]; old=u.get("total",0); u["total"]=old+amt; total=u["total"]
        if total>=100: u["level"]="vip"; u["verified"]=True; u["expires_at"]="lifetime"; new_lvl="VIP"
        elif total>=50: u["level"]="pro"; u["verified"]=True; new_lvl="PRO"
        elif total>=20: u["level"]="starter"; u["verified"]=True; new_lvl="STARTER"
        else: new_lvl="FREE"
        d[str(uid)]=u; save(d)
        try: bot.send_message(int(uid),f"💰 Deposit ${amt} Total ${total} Level {new_lvl} SUM!")
        except: pass
        try: bot.send_message(int(OWNER),f"💵 {uid} +${amt} Total ${total} {new_lvl}")
        except: pass
        return f"OK {uid} {old}->{total}",200
    except Exception as e: return f"Error {e}",500
@bot.message_handler(commands=["start","cancel","clearme"])
def start_cmd(m):
    chat_id=m.chat.id; uid=str(m.from_user.id)
    if m.text.startswith("/cancel"): broadcast_data.clear(); add_pending.clear(); bot.send_message(chat_id,"✅ Cancelled"); return
    u=ensure(uid); lvl=get_lvl(uid); lim_show="♾️ Unlimited" if lvl=="vip" else "5/day"
    txt=f"👋 Welcome {m.from_user.first_name}!\n👑 {lvl.upper()} 📊 {u.get('today',0)}/{lim_show}\n🔥 NEW PRO WARNINGS ACTIVE!"
    mm=bot.send_message(chat_id,txt,reply_markup=get_main_kb(uid))
    store_and_cleanup(chat_id,mm.message_id)
@bot.message_handler(content_types=["text","photo","video","document","animation"],func=is_owner_pending)
def owner_pending_handler(m):
    tid=str(m.from_user.id); chat_id=m.chat.id
    if tid in add_pending:
        uid_input=(m.text or "").strip().split()[0]
        if not uid_input.isdigit(): bot.send_message(chat_id,"❌ Numeric ID"); return
        d=load_db(); level=add_pending.get(tid); lvl_clean=level.lower().split("_")[0]
        mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
        d[uid_input]={"total":mp.get(lvl_clean,0),"level":"vip" if lvl_clean in ["vip","lifetime"] else lvl_clean if lvl_clean!="free" else "none","verified":lvl_clean!="free","today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
        save(d); add_pending.pop(tid,None); bot.send_message(chat_id,f"✅ ADD {uid_input} as {lvl_clean}"); return
    if tid in broadcast_data:
        target=broadcast_data.get(tid); tval=target["target"] if isinstance(target,dict) else target
        data={"target":tval}
        if m.content_type=="photo": data["type"]="photo"; data["file_id"]=m.photo[-1].file_id; data["caption"]=m.caption or ""
        elif m.content_type=="video": data["type"]="video"; data["file_id"]=m.video.file_id; data["caption"]=m.caption or ""
        else: data["type"]="text"; data["text"]=m.text or ""
        data["target"]=tval; broadcast_data[tid]=data
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("No Delete",callback_data="del_none")); k.add(types.InlineKeyboardButton("1 Week",callback_data="del_7"))
        bot.send_message(chat_id,f"Saved {tval}",reply_markup=k); return
@bot.message_handler(func=lambda m: True)
def text_handler(m):
    chat_id=m.chat.id; uid=str(m.from_user.id); txt=(m.text or "").strip()
    if not txt or txt.startswith("/"): return
    ensure(uid); lvl=get_lvl(uid)
    if "Get Signal" in txt:
        k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
        mm=bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
    if "Deposit" in txt and "Upgrade" not in txt:
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("💰 Deposit",url=LINK+"?click_id="+uid))
        mm=bot.send_message(chat_id,f"💰 {LINK}?click_id={uid}",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
    if "Status" in txt:
        u=ensure(uid); mm=bot.send_message(chat_id,f"ID:{uid} Level:{lvl} Total:${u.get('total',0)} W/L:{u.get('today_wins',0)}W-{u.get('today_losses',0)}L"); store_and_cleanup(chat_id,mm.message_id); return
    if "Upgrade" in txt:
        u=ensure(uid); dep=u.get('total',0); need100=max(0,100-dep)
        txt_up=f"🚀 UPGRADE {lvl.upper()} Total ${dep} Need ${need100} for VIP"
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton(f"VIP Need ${need100}",url=LINK+"?click_id="+uid))
        mm=bot.send_message(chat_id,txt_up,reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
    if "Admin" in txt and uid==OWNER:
        k2=types.InlineKeyboardMarkup(row_width=2); k2.add(types.InlineKeyboardButton("Add User",callback_data="ad_adduser")); k2.add(types.InlineKeyboardButton("Broadcast",callback_data="ad_broad"))
        mm=bot.send_message(chat_id,f"ADMIN {len(load_db())}",reply_markup=k2); store_and_cleanup(chat_id,mm.message_id); return

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    try:
        bot.answer_callback_query(c.id)
        tid=str(c.from_user.id); data=c.data; chat_id=c.message.chat.id
        ensure(tid); lvl=get_lvl(tid)
        if data in ["res_win","res_loss"]:
            dbb=load_db(); ud=dbb.get(tid)
            if not ud: ud=ensure(tid)
            if data=="res_win":
                ud["wins"]=ud.get("wins",0)+1; ud["today_wins"]=ud.get("today_wins",0)+1; ud["win_streak"]=ud.get("win_streak",0)+1; ud["loss_streak"]=0; dbb[tid]=ud; save(dbb)
                ws=ud.get("win_streak",0)
                win_msgs=[
                    f"✅ BOOM! WIN! 🔥💰\n🏆 Streak: {ws} Wins!\n🚀 Keep pushing VIP!",
                    f"✅ PERFECT WIN! 💎🔥\n📈 {ws} in a row! You're on fire!",
                    f"✅ KAZI WIN! 👑💸\n🔥 Win streak {ws} - Machine!",
                    f"✅ BANG! WIN CONFIRMED! 🚀\n💰 {ws} Wins straight! Keep going!"
                ]
                msg=random.choice(win_msgs)
                mm=bot.send_message(chat_id,msg,reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
            else:
                ud["losses"]=ud.get("losses",0)+1; ud["today_losses"]=ud.get("today_losses",0)+1; ud["loss_streak"]=ud.get("loss_streak",0)+1; ud["win_streak"]=0; dbb[tid]=ud; save(dbb)
                ls=ud.get("loss_streak",0)
                if ls<=2:
                    loss12=[
                        f"❌ Loss, but we learn! 📚\n💪 Loss streak {ls} - Next is WIN for sure!",
                        f"❌ Not today, but we fight! ⚔️\n🔥 {ls} loss - Market trick, we adapt!",
                        f"❌ Small loss! 💸\n🚀 Top traders lose too, WIN coming!"
                    ]
                    msg=random.choice(loss12)
                elif ls==3:
                    msg=f"❌ 3 Losses in row 😤\n🧠 Don't revenge trade! Take small break\n💪 Next is WIN, trust KAZI!"
                elif ls==4:
                    msg=f"❌ 4 Losses 💔\n⚠️ Slow down boss! Reduce lot size\n🔥 We recover together!"
                elif ls==5:
                    msg=f"❌ 5 Losses in row! 🚨\n🛑 Almost at limit! 1 more = STOP\n🧘 Breathe, next will recover!"
                else:
                    msg=f"⚠️ WARNING! 6 LOSS STREAK 🚫\n\n🧠 Boss, STOP trading now!\n📉 Market is bad today, take a break!\n☕️ Rest 1 hour, clear mind!\n🔄 Come back fresh = WIN again!\n\n💡 Pro traders know when to STOP!\n🛑 Paused for your safety!"
                mm=bot.send_message(chat_id,msg,reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
        if tid==OWNER and data.startswith("addlvl_"): level=data.replace("addlvl_",""); add_pending[tid]=level; bot.send_message(chat_id,f"Level {level} Send ID"); return
        if tid==OWNER and data.startswith("broad_"): target=data.replace("broad_",""); broadcast_data[tid]={"target":target,"type":"pending"}; bot.send_message(chat_id,f"Target {target} Send msg"); return
        if tid==OWNER and data.startswith("del_"):
            content=broadcast_data.get(tid)
            if not content: bot.send_message(chat_id,"No content"); return
            cnt=0
            for uid in list(load_db().keys()):
                try:
                    if content.get("type")=="photo": bot.send_photo(uid,content["file_id"],caption=content.get("caption",""))
                    else: bot.send_message(uid,content.get("text",""))
                    cnt+=1; time.sleep(0.05)
                except: pass
            bot.send_message(chat_id,f"Sent {cnt}"); broadcast_data.pop(tid,None); return
        if tid==OWNER and data=="ad_adduser":
            kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("FREE",callback_data="addlvl_free")); kb.add(types.InlineKeyboardButton("STARTER",callback_data="addlvl_starter")); kb.add(types.InlineKeyboardButton("PRO",callback_data="addlvl_pro")); kb.add(types.InlineKeyboardButton("VIP",callback_data="addlvl_vip"))
            bot.send_message(chat_id,"Select level",reply_markup=kb); return
        if tid==OWNER and data=="ad_broad":
            kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("ALL",callback_data="broad_ALL")); kb.add(types.InlineKeyboardButton("VIP",callback_data="broad_VIP"))
            bot.send_message(chat_id,"Target?",reply_markup=kb); return
        if data=="sel_market":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
            mm=bot.send_message(chat_id,"Select Market",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="m_real":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("Auto",callback_data="real_auto"))
            mm=bot.send_message(chat_id,"REAL 15",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="m_otc":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("Auto 30",callback_data="otc_auto"))
            mm=bot.send_message(chat_id,"OTC 30",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="real_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in REAL: k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_REAL"))
            mm=bot.send_message(chat_id,"Pick REAL",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="otc_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[:15]: k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("Next 15",callback_data="otc_manual2"))
            mm=bot.send_message(chat_id,"OTC 1/2",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="otc_manual2":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[15:]: k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("Back",callback_data="otc_manual"))
            mm=bot.send_message(chat_id,"OTC 2/2",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data.startswith("pair_"):
            rest=data[5:]; pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}"); return
            k=types.InlineKeyboardMarkup(row_width=4); k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5"))
            mm=bot.send_message(chat_id,f"{pair} Pick Expiry",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data in ["real_auto","otc_auto"]:
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}"); return
            pairs=OTC if data.startswith("otc_") else REAL; pair=random.choice(pairs); exp=random.choice(EXP); sig,rsi,trend,conf=get_sig(pair,exp,lvl); inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% {pair} {sig} {exp} {cur+1}/{lim}",reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
        if data.startswith("sig_"):
            tmp=data[4:]; idx=tmp.rfind("_M"); pair=tmp[:idx]; exp=tmp[idx+1:]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}"); return
            sig,rsi,trend,conf=get_sig(pair,exp,lvl); inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% {pair} {sig} {exp} {cur+1}/{lim}",reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
    except Exception as e: print(f"CB ERR {e}")

def run_bot():
    while True:
        try:
            try: bot.remove_webhook()
            except: pass
            time.sleep(1)
            print("Starting polling V12.6.5 NEW WARNINGS")
            bot.infinity_polling(skip_pending=True,timeout=20)
        except Exception as e:
            print(f"Crash {e}"); time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",8080)))
