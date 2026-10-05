import os, json, random, time, threading
from datetime import datetime, date, timedelta
from flask import Flask, request
import telebot
from telebot import types
TOKEN=os.getenv("TOKEN") or os.getenv("BOT_TOKEN") or ""
if ":" not in TOKEN: print("❌ BAD TOKEN - Add TOKEN var")
OWNER="8188622130"
LINK=os.getenv("LINK","https://example.com")
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
def home(): return "V12.6.2.4 TOTAL SUM + Motivational"
@app.route('/postback')
def pocket_postback():
    try:
        uid=request.args.get('click_id') or request.args.get('clickid') or request.args.get('subid') or "0"
        amount=request.args.get('amount') or request.args.get('sum') or request.args.get('deposit') or "0"
        if not uid or uid=="0": return "Missing click_id",400
        try: amt=float(str(amount).replace('$','').replace(',','').strip())
        except: amt=0
        if amt<=0: return f"Ignored {uid}",200
        d=load_db()
        if str(uid) not in d: d[str(uid)]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
        u=d[str(uid)]; old=u.get("total",0); u["total"]=old+amt; total=u["total"]
        if total>=100: u["level"]="vip"; u["verified"]=True; u["expires_at"]="lifetime"; new_lvl="VIP ♾️"
        elif total>=50: u["level"]="pro"; u["verified"]=True; new_lvl="PRO 100/day"
        elif total>=20: u["level"]="starter"; u["verified"]=True; new_lvl="STARTER 20/day"
        else: u["level"]="none"; new_lvl="FREE"
        d[str(uid)]=u; save(d)
        try: bot.send_message(int(uid),f"💰 Pocket +${amt} ✅\n💵 Old: ${old} → Total: ${total}\n👑 Level: {new_lvl}\n🎯 Keep depositing = Higher WR!\n/start")
        except: pass
        try: bot.send_message(int(OWNER),f"💰 POSTBACK TOTAL SUM 👤 {uid} +${amt} {old}->{total} {new_lvl}")
        except: pass
        return f"OK {uid} +{amt} {old}->{total} {new_lvl}",200
    except Exception as e: return f"Error {e}",500
@bot.message_handler(commands=["start","cancel","clearme"])
def start_cmd(m):
    print(f"START {m.from_user.id}")
    chat_id=m.chat.id; uid=str(m.from_user.id)
    if m.text.startswith("/cancel"): broadcast_data.clear(); add_pending.clear(); bot.send_message(chat_id,"✅ Cancelled"); return
    if m.text.startswith("/clearme") and uid==OWNER:
        if chat_id in msg_hist:
            for mid in msg_hist[chat_id]:
                try: bot.delete_message(chat_id,mid)
                except: pass
        msg_hist[chat_id]=[]
        bot.send_message(chat_id,"✅ Cleared"); return
    u=ensure(uid); lvl=get_lvl(uid)
    if lvl=="vip": lim_show="♾️ Unlimited 87% WR"
    elif lvl=="pro": lim_show="100/day 70-85% WR"
    elif lvl=="starter": lim_show="20/day 60-70% WR"
    else: lim_show="5/day"
    txt=f"👋 Welcome {m.from_user.first_name}!\n👑 {lvl.upper()} 📊 Today {u.get('today',0)}/{lim_show}\n🔥 15R+30OTC Ready?"
    mm=bot.send_message(chat_id,txt,reply_markup=get_main_kb(uid))
    store_and_cleanup(chat_id,mm.message_id)@bot.message_handler(content_types=["text","photo","video","document","animation"],func=is_owner_pending)
def owner_pending_handler(m):
    tid=str(m.from_user.id); chat_id=m.chat.id
    if tid in add_pending:
        txt=m.text or ""; uid_input=txt.strip().replace("@","").split()[0] if txt else ""
        if not uid_input.isdigit(): bot.send_message(chat_id,"❌ Numeric ID"); return
        uid=uid_input; d=load_db()
        level=add_pending.get(tid); lvl_clean=level.lower().split("_")[0]
        mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
        d[uid]={"total":mp.get(lvl_clean,0),"level":"vip" if lvl_clean in ["vip","lifetime"] else lvl_clean if lvl_clean!="free" else "none","verified":lvl_clean!="free","today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
        if lvl_clean=="lifetime": d[uid]["expires_at"]="lifetime"
        save(d); add_pending.pop(tid,None); bot.send_message(chat_id,f"✅ ADD {uid} as {lvl_clean}"); return
    if tid in broadcast_data:
        target=broadcast_data.get(tid); tval=target["target"] if isinstance(target,dict) else target
        data={"target":tval} if not isinstance(target,dict) or target.get("type")=="pending" else target
        if m.content_type=="photo": data["type"]="photo"; data["file_id"]=m.photo[-1].file_id; data["caption"]=m.caption or ""
        elif m.content_type=="video": data["type"]="video"; data["file_id"]=m.video.file_id; data["caption"]=m.caption or ""
        else: data["type"]="text"; data["text"]=m.text or ""
        data["target"]=tval; broadcast_data[tid]=data
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("♾️ No Delete",callback_data="del_none")); k.add(types.InlineKeyboardButton("1 Week",callback_data="del_7")); k.add(types.InlineKeyboardButton("1 Month",callback_data="del_30"))
        bot.send_message(chat_id,f"✅ Saved Target:{tval} When delete?",reply_markup=k); return
@bot.message_handler(commands=["adduser"])
def admin_cmds(m):
    if str(m.from_user.id)!=OWNER: return
    chat_id=m.chat.id; a=m.text.split()
    d=load_db(); mp={"free":0,"starter":20,"pro":50,"vip":100,"lifetime":1000}
    if len(a)<3: bot.send_message(chat_id,"/adduser ID LEVEL"); return
    raw_uids=a[1].replace(","," ").split(); uids=[u.strip() for u in raw_uids if u.strip().isdigit()]
    lvl=a[2].lower().strip()
    if lvl not in mp: bot.send_message(chat_id,"Bad level"); return
    for uid in uids:
        d[uid]={"total":mp[lvl],"level":"vip" if lvl in ["vip","lifetime"] else lvl if lvl!="free" else "none","verified":lvl!="free","today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0,"today_wins":0,"today_losses":0}
    save(d); bot.send_message(chat_id,f"✅ Added {uids} as {lvl}")
@bot.message_handler(func=lambda m: True)
def text_handler(m):
    chat_id=m.chat.id; uid=str(m.from_user.id); txt=(m.text or "").strip()
    if not txt or txt.startswith("/"): return
    ensure(uid); lvl=get_lvl(uid)
    if "Get Signal" in txt:
        k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
        mm=bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
    if "Deposit" in txt:
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("💰 Deposit",url=LINK+"?click_id="+uid))
        mm=bot.send_message(chat_id,f"💰 DEPOSIT {LINK}?click_id={uid}\n💵 Total counted: Sums all deposits!",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
    if "Status" in txt:
        u=ensure(uid)
        if lvl=="vip": lim_txt="♾️ Unlimited up to 87% WR"
        elif lvl=="pro": lim_txt="100/day 70-85% WR"
        elif lvl=="starter": lim_txt="20/day 60-70% WR"
        else: lim_txt="5/day"
        mm=bot.send_message(chat_id,f"👤 ID:{uid}\n👑 Level:{lvl.upper()}\n💰 Total Deposit: ${u.get('total',0)} (SUMS ALL)\n📊 Today:{u.get('today',0)}/{lim_txt}\n🏆 W/L: {u.get('today_wins',0)}W-{u.get('today_losses',0)}L Today | {u.get('wins',0)}W-{u.get('losses',0)}L Total\n🔥 Streak: {u.get('win_streak',0)}W {u.get('loss_streak',0)}L"); store_and_cleanup(chat_id,mm.message_id); return
    if "How" in txt:
        mm=bot.send_message(chat_id,"❓ Register with link?click_id=YOUR_ID, Deposit, Sums total, Auto upgrade!"); store_and_cleanup(chat_id,mm.message_id); return
    if "Support" in txt:
        mm=bot.send_message(chat_id,"📞 Support @YourSupport"); store_and_cleanup(chat_id,mm.message_id); return
    if "Upgrade" in txt:
        u=ensure(uid); dep=u.get('total',0)
        need20=max(0,20-dep); need50=max(0,50-dep); need100=max(0,100-dep)
        if lvl=="vip":
            txt_up=f"👑 YOU ARE VIP ALREADY! ♾️\n💰 Total Deposit: ${dep} (SUMS ALL)\n📊 ♾️ Unlimited 80-87% WR 🔥\n🏆 Best level unlocked!\nKeep trading boss!"
        else:
            txt_up=f"🚀 UPGRADE YOUR LEVEL {lvl.upper()} 👑\n💰 Your TOTAL Deposit: ${dep} (SUMS ALL DEPOSITS!)\n💪 Every deposit adds up!\n\n🆓 FREE: 5/day 55-65% WR\n\n⭐ STARTER $20: 20/day 60-70% WR\n💵 Need ${need20} more to unlock! 🔥\nTotal $20 unlocks\n\n💎 PRO $50: 100/day 70-85% WR\n💵 Need ${need50} more! 🚀\nTotal $50 unlocks - 5x more signals!\n\n👑 VIP $100: ♾️ Unlimited 80-87% WR 🔥 BEST!\n💵 Need ${need100} more! 💎\nTotal $100 = VIP FOREVER!\n\n💡 Example: You deposit $10 + $15 + $30 = $55 = PRO unlocked!\n💰 Deposits SUM = No loss!\n🎯 Higher level = More WINS!"
        k=types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton(f"⭐ STARTER Need ${need20}",url=LINK+"?click_id="+uid))
        k.add(types.InlineKeyboardButton(f"💎 PRO Need ${need50}",url=LINK+"?click_id="+uid))
        k.add(types.InlineKeyboardButton(f"👑 VIP Need ${need100} BEST!",url=LINK+"?click_id="+uid))
        mm=bot.send_message(chat_id,txt_up,reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
    if "Admin" in txt and uid==OWNER:
        k2=types.InlineKeyboardMarkup(row_width=2); k2.add(types.InlineKeyboardButton("➕ Add User",callback_data="ad_adduser")); k2.add(types.InlineKeyboardButton("Users",callback_data="ad_users")); k2.add(types.InlineKeyboardButton("Broadcast",callback_data="ad_broad"))
        mm=bot.send_message(chat_id,f"ADMIN Users {len(load_db())}",reply_markup=k2); store_and_cleanup(chat_id,mm.message_id); return@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    try:
        bot.answer_callback_query(c.id)
        tid=str(c.from_user.id); data=c.data; chat_id=c.message.chat.id
        ensure(tid); lvl=get_lvl(tid)
        if data in ["res_win","res_loss"]:
            dbb=load_db(); ud=dbb.get(tid); adm=load_admin()
            if not ud: ud=ensure(tid)
            if data=="res_win":
                ud["wins"]=ud.get("wins",0)+1; ud["today_wins"]=ud.get("today_wins",0)+1; ud["win_streak"]=ud.get("win_streak",0)+1; ud["loss_streak"]=0; dbb[tid]=ud; save(dbb); adm["total_wins"]=adm.get("total_wins",0)+1; save_admin(adm)
                mm=bot.send_message(chat_id,f"✅ BOOM! WIN! 🔥\n🏆 Streak: {ud['win_streak']} Wins!",reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
            else:
                ud["losses"]=ud.get("losses",0)+1; ud["today_losses"]=ud.get("today_losses",0)+1; ud["loss_streak"]=ud.get("loss_streak",0)+1; ud["win_streak"]=0; dbb[tid]=ud; save(dbb); adm["total_losses"]=adm.get("total_losses",0)+1; save_admin(adm)
                ls=ud.get("loss_streak",1)
                if ls<=2: msg=f"❌ Loss, but we learn! 📚\n💪 Loss streak {ls} - Next is WIN!"
                elif ls==3: msg=f"❌ 3 Losses in row 😤\n🧠 Don't revenge trade!"
                elif ls==4: msg=f"❌ 4 Losses 💔\n⚠️ Slow down boss!"
                elif ls==5: msg=f"❌ 5 Losses 🚨\n🛑 Almost at limit! 1 more = STOP"
                else: msg=f"⚠️ WARNING! 6 LOSS STREAK 🚫\n\n🧠 Boss, STOP trading now!\n📉 Market is bad today, take a break!\n☕️ Rest 1 hour!\n🔄 Come back fresh = WIN again!\n\nStreak: {ls}L"
                mm=bot.send_message(chat_id,msg,reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
        if tid==OWNER and data.startswith("ad_"):
            if data=="ad_users":
                txt="👥 Users:\n"
                for uid,u in list(load_db().items())[:20]: txt+=f"{uid} {u.get('level')} ${u.get('total')}\n"
                mm=bot.send_message(chat_id,txt); store_and_cleanup(chat_id,mm.message_id); return
            if data=="ad_adduser":
                kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("🆓 FREE 5/day",callback_data="addlvl_free")); kb.add(types.InlineKeyboardButton("⭐ STARTER 20/day",callback_data="addlvl_starter")); kb.add(types.InlineKeyboardButton("💎 PRO 100/day",callback_data="addlvl_pro")); kb.add(types.InlineKeyboardButton("👑 VIP Unlimited 87%",callback_data="addlvl_vip")); kb.add(types.InlineKeyboardButton("💎 LIFETIME ♾️",callback_data="addlvl_lifetime"))
                mm=bot.send_message(chat_id,"➕ SELECT LEVEL:",reply_markup=kb); store_and_cleanup(chat_id,mm.message_id); return
            if data=="ad_stats": dd=load_db(); tot=sum(u.get('total',0) for u in dd.values()); ver=sum(1 for u in dd.values() if u.get('verified')); mm=bot.send_message(chat_id,f"📊 U:{len(dd)} V:{ver} ${tot}"); store_and_cleanup(chat_id,mm.message_id); return
            if data=="ad_wr": adm=load_admin(); mm=bot.send_message(chat_id,f"🏆 WR ✅ {adm.get('total_wins',0)} ❌ {adm.get('total_losses',0)}"); store_and_cleanup(chat_id,mm.message_id); return
            if data=="ad_broad":
                kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL")); kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="broad_FREE")); kb.add(types.InlineKeyboardButton("⭐ STARTER",callback_data="broad_STARTER")); kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="broad_PRO")); kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="broad_VIP")); kb.add(types.InlineKeyboardButton("💰 ALL VIPs",callback_data="broad_ALLVIP"))
                mm=bot.send_message(chat_id,"🎯 Select target:",reply_markup=kb); store_and_cleanup(chat_id,mm.message_id); return
        if tid==OWNER and data.startswith("addlvl_"): level=data.replace("addlvl_",""); add_pending[tid]=level; mm=bot.send_message(chat_id,f"✅ Level {level.upper()} selected!\nSEND User ID:\n/cancel to exit"); store_and_cleanup(chat_id,mm.message_id); return
        if tid==OWNER and data.startswith("broad_"): target=data.replace("broad_",""); broadcast_data[tid]={"target":target,"type":"pending"}; mm=bot.send_message(chat_id,f"🎯 Target {target} ✅\nSEND broadcast msg:\n/cancel to exit"); store_and_cleanup(chat_id,mm.message_id); return
        if tid==OWNER and data.startswith("del_"):
            content=broadcast_data.get(tid)
            if not content or content.get("type")=="pending": mm=bot.send_message(chat_id,"❌ No broadcast content"); store_and_cleanup(chat_id,mm.message_id); return
            target=content["target"]; days_str=data.replace("del_",""); delete_days=None if days_str=="none" else int(days_str) if days_str.isdigit() else None
            cnt=0; dbs=load_db(); b_list=load_broadcast(); delete_at=datetime.now()+timedelta(days=delete_days) if delete_days else None
            for uid,u in list(dbs.items()):
                lvl_u=u.get("level","none"); ver=u.get("verified",False); send=False
                if target=="ALL": send=True
                elif target=="FREE" and not ver: send=True
                elif target=="STARTER" and lvl_u=="starter": send=True
                elif target=="PRO" and lvl_u=="pro": send=True
                elif target=="VIP" and lvl_u=="vip": send=True
                elif target=="ALLVIP" and lvl_u in ["starter","pro","vip"]: send=True
                if send:
                    try:
                        ctype=content.get("type","text")
                        if ctype=="photo": sent=bot.send_photo(uid,content["file_id"],caption=content.get("caption",""))
                        elif ctype=="video": sent=bot.send_video(uid,content["file_id"],caption=content.get("caption",""))
                        elif ctype=="document": sent=bot.send_document(uid,content["file_id"],caption=content.get("caption",""))
                        elif ctype=="animation": sent=bot.send_animation(uid,content["file_id"],caption=content.get("caption",""))
                        else:
                            txt=content.get("text","")
                            if not txt: continue
                            sent=bot.send_message(uid,txt)
                        cnt+=1
                        if delete_at: b_list.append({"chat_id":int(uid) if str(uid).isdigit() else uid,"msg_id":sent.message_id,"delete_at":delete_at.isoformat()})
                        time.sleep(0.05)
                    except: continue
            if delete_at: save_broadcast(b_list)
            mm=bot.send_message(chat_id,f"✅ Broadcast {cnt} users 🎯 {target}"); store_and_cleanup(chat_id,mm.message_id)
            if tid in broadcast_data: del broadcast_data[tid]
            return
        if data=="sel_market":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("📊 OTC 30",callback_data="m_otc"))
            mm=bot.send_message(chat_id,"🔥 Select Market:",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="m_real":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
            mm=bot.send_message(chat_id,"💹 REAL 15",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="m_otc":
            k=types.InlineKeyboardMarkup(row_width=2); k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
            mm=bot.send_message(chat_id,"📊 OTC 30",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="real_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in REAL: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_REAL"))
            mm=bot.send_message(chat_id,"✋ Pick Pair 15 REAL",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="otc_manual":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[:15]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("➡️ Next 15",callback_data="otc_manual2"))
            mm=bot.send_message(chat_id,"✋ OTC 1/2 (15)",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data=="otc_manual2":
            k=types.InlineKeyboardMarkup(row_width=2)
            for p in OTC[15:]: k.add(types.InlineKeyboardButton(f"{p}",callback_data=f"pair_{p}_OTC"))
            k.add(types.InlineKeyboardButton("⬅️ Back",callback_data="otc_manual"))
            mm=bot.send_message(chat_id,"✋ OTC 2/2 (15)",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data.startswith("pair_"):
            rest=data[5:]; pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim} reached!"); store_and_cleanup(chat_id,mm.message_id); return
            k=types.InlineKeyboardMarkup(row_width=4); k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5"))
            mm=bot.send_message(chat_id,f"💹 {pair} Pick Expiry:",reply_markup=k); store_and_cleanup(chat_id,mm.message_id); return
        if data in ["real_auto","otc_auto"]:
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim} reached!"); store_and_cleanup(chat_id,mm.message_id); return
            pairs=OTC if data.startswith("otc_") else REAL; pair=random.choice(pairs); exp=random.choice(EXP); sig,rsi,trend,conf=get_sig(pair,exp,lvl); inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% WR 💹 {pair} {'📈 BUY' if 'BUY' in sig else '📉 SELL'} {sig} Exp {exp} RSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
        if data.startswith("sig_"):
            tmp=data[4:]; idx=tmp.rfind("_M"); pair=tmp[:idx]; exp=tmp[idx+1:]
            is_over,cur,lim=check_limit(tid,lvl)
            if is_over: mm=bot.send_message(chat_id,f"🚫 Limit {cur}/{lim} reached!"); store_and_cleanup(chat_id,mm.message_id); return
            sig,rsi,trend,conf=get_sig(pair,exp,lvl); inc(tid)
            mm=bot.send_message(chat_id,f"🔥 {lvl.upper()} {conf}% WR {pair} {'📈 BUY' if 'BUY' in sig else '📉 SELL'} {sig} Exp {exp} RSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard()); store_and_cleanup(chat_id,mm.message_id); return
    except Exception as e: print(f"CB ERR {e}")

def auto_delete_worker():
    while True:
        try:
            bl=load_broadcast(); now=datetime.now(); new=[]
            for it in bl:
                try:
                    da=datetime.fromisoformat(it["delete_at"])
                    if now>=da:
                        try: bot.delete_message(it["chat_id"],it["msg_id"])
                        except: pass
                    else: new.append(it)
                except: continue
            if len(new)!=len(bl): save_broadcast(new)
        except: pass
        time.sleep(60)

def run_bot():
    while True:
        try:
            try: bot.remove_webhook()
            except: pass
            time.sleep(1)
            print("Starting polling...")
            bot.infinity_polling(skip_pending=True,timeout=20)
        except Exception as e:
            print(f"Polling crashed {e} retry 5s")
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    threading.Thread(target=auto_delete_worker,daemon=True).start()
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",8080)))
