import os, random, time, threading
from datetime import datetime, timezone
from flask import Flask, request
import telebot
from telebot import types

print("BOOTING V13.2.9 MINI...") # THIS MUST APPEAR IN LOGS

BOT_TOKEN=os.environ.get("BOT_TOKEN","")
if not BOT_TOKEN or len(BOT_TOKEN)<10:
    print("ERROR: BOT_TOKEN missing! Set in Railway Variables")
    BOT_TOKEN="123456:FAKE_TOKEN_FOR_BUILD"

OWNER_ID=8188622130
AFFILIATE_LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
pairs_real=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","GBP/JPY","AUD/JPY","EUR/AUD","USD/CHF","NZD/USD","EUR/CAD","GBP/CAD","AUD/CAD"]
pairs_otc=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/JPY OTC","EUR/GBP OTC","GBP/JPY OTC","AUD/JPY OTC","EUR/AUD OTC","USD/CHF OTC","NZD/USD OTC","EUR/CAD OTC","GBP/CAD OTC","AUD/CAD OTC","EUR/NZD OTC","GBP/NZD OTC","GBP/AUD OTC","AUD/NZD OTC","EUR/CHF OTC","GBP/CHF OTC","CHF/JPY OTC","AUD/CHF OTC","CAD/CHF OTC","USD/BRL OTC","EUR/BRL OTC","USD/INR OTC","USD/TRY OTC","EUR/TRY OTC","USD/ZAR OTC"]
MOTIV=["STAY STRONG","NEXT IS WIN","DON'T GIVE UP","FOCUS","YOU GOT THIS"]

bot=telebot.TeleBot(BOT_TOKEN)
app=Flask(__name__)
users={}
last={}
bwait={}

@app.route('/')
def home(): return "V13.2.9 MINI ALIVE"

def ensure(uid,name):
    if uid not in users:
        users[uid]={"name":name,"dep":0,"wins":0,"loss":0,"gw":0,"gl":0,"st":0,"ls":0,"lim":0,"used":0,"reset":datetime.now(timezone.utc).date().isoformat(),"ban":False,"bw":None,"reg":False}
    return users[uid]

def level(uid):
    if uid==OWNER_ID: return "VIP"
    if uid not in users: return "LOCKED"
    if not users[uid]["reg"]: return "LOCKED"
    d=users[uid]["dep"]
    if d>=100: return "VIP"
    if d>=50: return "PRO"
    if d>=20: return "STARTER"
    return "NONE"

def glim(l):
    return {"LOCKED":0,"NONE":5,"STARTER":20,"PRO":100,"VIP":999999}.get(l,0)

def daily(uid):
    t=datetime.now(timezone.utc).date().isoformat()
    if users[uid]["reset"]!=t:
        users[uid].update({"wins":0,"loss":0,"st":0,"ls":0,"used":0,"reset":t,"lim":glim(level(uid))})

@app.route('/postback')
def pb():
    try:
        uid=int(request.args.get('click_id')); dep=int(float(request.args.get('deposit','0')))
        ensure(uid,f"User{uid}"); users[uid]["reg"]=True; users[uid]["dep"]=max(users[uid]["dep"],dep); users[uid]["lim"]=glim(level(uid))
        return f"OK {uid} {level(uid)}",200
    except: return "ERR",400

def menu():
    m=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    m.add("📊 GET SIGNAL","✅ REAL 15"); m.add("🔶 OTC 30","💎 Upgrade"); m.add("💰 Deposit","📈 My Status"); m.add("📜 How it Works","👑 Admin Panel")
    return m

def locked(uid):
    sep='&' if '?' in AFFILIATE_LINK else '?'; link=f"{AFFILIATE_LINK}{sep}subid={uid}"
    mk=types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton("🔗 Register Now",url=link)); mk.add(types.InlineKeyboardButton("📜 How it Works",callback_data="how"))
    txt=f"🔒 LOCKED - Register to unlock\nLink: {link}\n1️⃣ Register?subid={uid}\n2️⃣ Get 5/day FREE\n3️⃣ Deposit upgrade"
    return txt,mk

def tr(cid,msg):
    last.setdefault(cid,[]).append(msg.message_id)
    if len(last[cid])>10: last[cid]=last[cid][-10:]

def clean(cid):
    for mid in last.get(cid,[]):
        try: bot.delete_message(cid,mid)
        except: pass
    last[cid]=[]

@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'], func=lambda m: bwait.get(m.from_user.id) or users.get(m.from_user.id,{}).get("bw"))
def bc(m):
    uid=m.from_user.id; w=bwait.get(uid) or users[uid]["bw"]
    if uid!=OWNER_ID: return
    hrs, target = w["h"], w["t"]; c,f=0,0; sent=[]
    for u_id in list(users.keys()):
        if u_id==OWNER_ID or users[u_id]["ban"]: continue
        if target!="ALL" and level(u_id)!=target: continue
        try:
            if m.content_type=='text': msg=bot.send_message(u_id,f"📢 ADMIN:\n\n{m.text}")
            else: msg=bot.copy_message(u_id,m.chat.id,m.message_id)
            if hrs>0: sent.append((u_id,msg.message_id)); c+=1
        except: f+=1
    bwait.pop(uid,None); users[uid]["bw"]=None
    bot.send_message(uid,f"✅ DONE Sent:{c} Fail:{f} Del:{hrs}h Target:{target}",reply_markup=menu())
    if hrs>0:
        def dl():
            time.sleep(hrs*3600)
            for cid,mid in sent:
                try: bot.delete_message(cid,mid)
                except: pass
        threading.Thread(target=dl,daemon=True).start()

def sig():
    rsi=round(random.uniform(20,80),1); pr=round(random.uniform(1.05,1.35),4); ema=round(pr+random.uniform(-0.015,0.015),4); ab=pr>ema
    if rsi<30: rl,rt=f"RSI {rsi} Oversold","bull"
    elif rsi<45: rl,rt=f"RSI {rsi} Bullish","bull"
    elif rsi<=55: rl,rt=f"RSI {rsi} Neutral","neu"
    elif rsi<=70: rl,rt=f"RSI {rsi} Bearish","bear"
    else: rl,rt=f"RSI {rsi} Overbought","bear"
    el=f"EMA200 {pr} Above 🔼" if ab else f"EMA200 {pr} Below 🔽"; et="bull" if ab else "bear"
    if rt=="bull" and et=="bull": d,s="BUY 📈","Strong Bullish 🔼🔼"
    elif rt=="bear" and et=="bear": d,s="SELL 📉","Strong Bearish 🔽🔽"
    elif rt=="bull": d,s="BUY 📈","Bullish 🔼"
    else: d,s="SELL 📉","Bearish 🔽"
    return d,s,rl,el

@bot.message_handler(func=lambda m: True, content_types=['text'])
def txt(m):
    uid=m.from_user.id; t=(m.text or "").upper()
    if bwait.get(uid) or users.get(uid,{}).get("bw"):
        if any(k in t for k in ["GET SIGNAL","REAL 15","OTC 30","UPGRADE","DEPOSIT","MY STATUS","HOW IT WORKS","ADMIN PANEL","/START"]):
            bwait.pop(uid,None)
            if uid in users: users[uid]["bw"]=None
        else: return
    if uid not in users: ensure(uid,m.from_user.username or m.from_user.first_name)
    if users[uid]["ban"]: bot.send_message(m.chat.id,"⛔ Banned"); return
    daily(uid); lv=level(uid)
    if lv=="LOCKED" and not any(k in t for k in ["HOW IT WORKS","ADMIN PANEL","/START"]):
        if any(k in t for k in ["GET SIGNAL","REAL 15","OTC 30","MY STATUS","UPGRADE","DEPOSIT"]):
            tx,mk=locked(uid); tr(m.chat.id, bot.send_message(m.chat.id,tx,reply_markup=mk)); return
    if "GET SIGNAL" in t:
        if lv=="LOCKED": tx,mk=locked(uid); tr(m.chat.id, bot.send_message(m.chat.id,tx,reply_markup=mk)); return
        clean(m.chat.id); mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("✅ REAL 15",callback_data="r15"),types.InlineKeyboardButton("🔶 OTC 30",callback_data="o30"))
        tr(m.chat.id, bot.send_message(m.chat.id,"🔥 Select Market:",reply_markup=mk))
    elif "REAL 15" in t:
        clean(m.chat.id); mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("✋ Manual",callback_data="man_r"),types.InlineKeyboardButton("🤖 Auto",callback_data="au_r"))
        tr(m.chat.id, bot.send_message(m.chat.id,"💹 REAL 15:",reply_markup=mk))
    elif "OTC 30" in t:
        clean(m.chat.id); mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("✋ Manual",callback_data="man_o"),types.InlineKeyboardButton("🤖 Auto",callback_data="au_o"))
        tr(m.chat.id, bot.send_message(m.chat.id,"🔶 OTC 30:",reply_markup=mk))
    elif "MY STATUS" in t:
        if lv=="LOCKED": tx,mk=locked(uid); tr(m.chat.id, bot.send_message(m.chat.id,tx,reply_markup=mk)); return
        tr(m.chat.id, bot.send_message(m.chat.id,f"📈 MY STATUS - RESET 00:00 UTC\n✅ Wins Today: {users[uid]['wins']}\n❌ Loss Today: {users[uid]['loss']}\n⏰ Resets daily",reply_markup=menu()))
    elif "UPGRADE" in t or "DEPOSIT" in t:
        sep='&' if '?' in AFFILIATE_LINK else '?'; link=f"{AFFILIATE_LINK}{sep}subid={uid}"
        mk=types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton("💰 Deposit Now",url=link))
        tr(m.chat.id, bot.send_message(m.chat.id,f"🚀 Current: {lv}\n⚪ NONE $0 5/day\n🟢 STARTER $20 20/day\n🔵 PRO $50 100/day\n💎 VIP $100 UNLIMITED\n🔗 {link}",reply_markup=mk))
    elif "HOW IT WORKS" in t:
        tr(m.chat.id, bot.send_message(m.chat.id,"📜 5 Steps:\n1️⃣ Register?subid=ID\n2️⃣ 5/day FREE\n3️⃣ Deposit upgrade\n4️⃣ GET SIGNAL\n5️⃣ Daily W/L reset 00:00 UTC",reply_markup=menu()))
    elif "ADMIN PANEL" in t:
        if uid!=OWNER_ID: return
        clean(m.chat.id); mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="adm_bc")); mk.add(types.InlineKeyboardButton("👥 Users",callback_data="adm_u"),types.InlineKeyboardButton("📊 Stats",callback_data="adm_s")); mk.add(types.InlineKeyboardButton("🏆 GWR",callback_data="adm_g"),types.InlineKeyboardButton("📈 Daily",callback_data="adm_d"))
        tr(m.chat.id, bot.send_message(m.chat.id,f"👑 ADMIN V13.2.9 MINI Total:{len(users)}",reply_markup=mk))
    elif t.startswith("/ADDUSER") or t.startswith("/SUCH") or t.startswith("/BAN") or t.startswith("/USERS") or t.startswith("/STATS"):
        adm(m)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid=c.from_user.id; data=c.data; chat=c.message.chat.id; ensure(uid,c.from_user.username or "U")
    if users[uid]["ban"]: return
    daily(uid); lv=level(uid)
    if data=="how":
        tr(chat, bot.send_message(chat,"📜 Register?subid=ID → 5/day FREE → Deposit upgrade",reply_markup=menu())); return
    if lv=="LOCKED" and data not in ["how","adm_bc","adm_u","adm_s","adm_g","adm_d","b24","b168","b0","ball","bnone","bsta","bpro","bvip","block"]:
        tx,mk=locked(uid); tr(chat, bot.send_message(chat,tx,reply_markup=mk)); return
    if data=="r15":
        clean(chat); mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("✋ Manual",callback_data="man_r"),types.InlineKeyboardButton("🤖 Auto",callback_data="au_r")); tr(chat, bot.send_message(chat,"💹 REAL 15:",reply_markup=mk))
    elif data=="o30":
        clean(chat); mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("✋ Manual",callback_data="man_o"),types.InlineKeyboardButton("🤖 Auto",callback_data="au_o")); tr(chat, bot.send_message(chat,"🔶 OTC 30:",reply_markup=mk))
    elif data.startswith("man_"):
        ty="real" if data=="man_r" else "otc"; sendp(chat,ty,0)
    elif data.startswith("pairs_"):
        _,ty,pg=data.split("_"); sendp(chat,ty,int(pg))
    elif data.startswith("pair_"):
        _,ty,pn=data.split("_",2); pn=pn.replace("_","/"); mk=types.InlineKeyboardMarkup(row_width=4); mk.add(types.InlineKeyboardButton("M1",callback_data=f"e_M1_{ty}_{pn}"),types.InlineKeyboardButton("M2",callback_data=f"e_M2_{ty}_{pn}"),types.InlineKeyboardButton("M3",callback_data=f"e_M3_{ty}_{pn}"),types.InlineKeyboardButton("M5",callback_data=f"e_M5_{ty}_{pn}")); tr(chat, bot.send_message(chat,f"📊 {pn} Expiry:",reply_markup=mk))
    elif data.startswith("e_"):
        _,exp,ty,pn=data.split("_",3); pn=pn.replace("_","/"); sends(chat,uid,pn,exp,ty)
    elif data.startswith("au_"):
        ty="real" if data=="au_r" else "otc"; lst=pairs_real if ty=="real" else pairs_otc; sends(chat,uid,random.choice(lst),"M1",ty)
    elif data=="next":
        clean(chat); mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("✅ REAL 15",callback_data="r15"),types.InlineKeyboardButton("🔶 OTC 30",callback_data="o30")); tr(chat, bot.send_message(chat,"🔥 Select:",reply_markup=mk))
    elif data=="win":
        users[uid]["wins"]+=1; users[uid]["gw"]+=1; users[uid]["st"]+=1; users[uid]["ls"]=0; tr(chat, bot.send_message(chat,f"BOOM WIN! 🔥 Streak {users[uid]['st']} | W:{users[uid]['wins']} L:{users[uid]['loss']}",reply_markup=menu()))
    elif data=="loss":
        users[uid]["loss"]+=1; users[uid]["gl"]+=1; users[uid]["ls"]+=1; users[uid]["st"]=0; ls=users[uid]["ls"]
        if ls>=6: txt=f"⚠️⚠️ MARKET NOT STABLE — STOP NOW! ⚠️⚠️\n💔 {ls} LOSS ROW!\n☕ BREAK 30-60min! W:{users[uid]['wins']} L:{users[uid]['loss']}"
        else: txt=f"💔 LOSS {ls}/5 — {random.choice(MOTIV)} Next WIN! W:{users[uid]['wins']} L:{users[uid]['loss']}"
        tr(chat, bot.send_message(chat,txt,reply_markup=menu()))
    elif data=="adm_u": adm(c.message,True)
    elif data=="adm_s": adm(c.message,True,True)
    elif data=="adm_g":
        if uid!=OWNER_ID: return
        tw=sum(u["gw"] for u in users.values()); tl=sum(u["gl"] for u in users.values()); tot=tw+tl; wr=round(tw/tot*100,2) if tot else 0
        tr(chat, bot.send_message(chat,f"🏆 GWR NEVER RESET\nW:{tw} L:{tl} WR:{wr}%",reply_markup=menu()))
    elif data=="adm_d":
        if uid!=OWNER_ID: return
        tw=sum(u["wins"] for u in users.values()); tl=sum(u["loss"] for u in users.values())
        tr(chat, bot.send_message(chat,f"📈 DAILY RESET 00:00 UTC\nW:{tw} L:{tl}",reply_markup=menu()))
    elif data=="adm_bc":
        if uid!=OWNER_ID: return
        mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("📅 1 Day",callback_data="b24"),types.InlineKeyboardButton("📅 1 Week",callback_data="b168"),types.InlineKeyboardButton("♾️ Never",callback_data="b0")); tr(chat, bot.send_message(chat,"⏰ DELETE PERIOD:",reply_markup=mk))
    elif data.startswith("b24") or data.startswith("b168") or data.startswith("b0"):
        if uid!=OWNER_ID: return
        h=int(data[1:]); mk=types.InlineKeyboardMarkup(row_width=3); mk.add(types.InlineKeyboardButton("ALL",callback_data=f"ball_{h}"),types.InlineKeyboardButton("NONE",callback_data=f"bnone_{h}"),types.InlineKeyboardButton("STARTER",callback_data=f"bsta_{h}")); mk.add(types.InlineKeyboardButton("PRO",callback_data=f"bpro_{h}"),types.InlineKeyboardButton("VIP",callback_data=f"bvip_{h}"),types.InlineKeyboardButton("LOCKED",callback_data=f"block_{h}")); tr(chat, bot.send_message(chat,f"Target for {h}h:",reply_markup=mk))
    elif data.startswith("ball_") or data.startswith("bnone_") or data.startswith("bsta_") or data.startswith("bpro_") or data.startswith("bvip_") or data.startswith("block_"):
        if uid!=OWNER_ID: return
        parts=data.split("_"); target=parts[0][1:].upper(); hrs=int(parts[1]); bwait[uid]={"h":hrs,"t":target}; users[uid]["bw"]={"h":hrs,"t":target}; tr(chat, bot.send_message(chat,f"✍️ DONE {hrs}h {target} Now send file ANY type!",reply_markup=menu()))

def sendp(cid,ty,pg):
    lst=pairs_real if ty=="real" else pairs_otc; per=10; s=pg*per; e=s+per
    mk=types.InlineKeyboardMarkup(row_width=2)
    for p in lst[s:e]: mk.add(types.InlineKeyboardButton(p,callback_data=f"pair_{ty}_{p.replace('/','_')}"))
    nav=[]
    if pg>0: nav.append(types.InlineKeyboardButton("⬅️",callback_data=f"pairs_{ty}_{pg-1}"))
    if e<len(lst): nav.append(types.InlineKeyboardButton("➡️",callback_data=f"pairs_{ty}_{pg+1}"))
    if nav: mk.row(*nav)
    tr(cid, bot.send_message(cid,f"📊 {ty} Page {pg+1}",reply_markup=mk))

def sends(cid,uid,pair,exp,ty):
    daily(uid); lv=level(uid)
    if users[uid]["used"]>=users[uid]["lim"]:
        sep='&' if '?' in AFFILIATE_LINK else '?'; link=f"{AFFILIATE_LINK}{sep}subid={uid}"; mk=types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton("🚀 UPGRADE",url=link))
        tx=f"⛔ LIMIT {users[uid]['used']}/{users[uid]['lim']} Upgrade VIP UNLIMITED {link}"; tr(cid, bot.send_message(cid,tx,reply_markup=mk)); return
    users[uid]["used"]+=1; d,s,rl,el=sig(); lim="∞" if lv=="VIP" else str(users[uid]["lim"])
    mk=types.InlineKeyboardMarkup(row_width=2); mk.add(types.InlineKeyboardButton("✅ WIN",callback_data="win"),types.InlineKeyboardButton("❌ LOSS",callback_data="loss")); mk.add(types.InlineKeyboardButton("🔥 Next",callback_data="next"))
    txt=f"🔥 {lv} {'🔶' if 'OTC' in pair else '✅'}\n📊 {pair}\n📈 {d} - {s}\n⏰ {exp}\n📉 {rl}\n📊 {el}\n📊 {users[uid]['used']}/{lim} Today"
    tr(cid, bot.send_message(cid,txt,reply_markup=mk))

def adm(m,is_cb=False,is_st=False):
    uid=m.from_user.id if not is_cb else m.chat.id
    if uid!=OWNER_ID: return
    t=m.text or ""; up=t.upper()
    if up.startswith("/ADDUSER"):
        p=t.split()
        if len(p)<3: bot.send_message(m.chat.id,"Use: /adduser ID 50"); return
        try: tid=int(p[1]); dep=int(p[2])
        except: bot.send_message(m.chat.id,"Invalid"); return
        ensure(tid,f"User{tid}"); users[tid]["reg"]=True; users[tid]["dep"]=dep; users[tid]["lim"]=glim(level(tid)); bot.send_message(m.chat.id,f"✅ {tid} Level {level(tid)}")
        return
    if up.startswith("/SUCH") or up.startswith("/SEARCH"):
        p=t.split()
        if len(p)<2: return
        try: tid=int(p[1])
        except: return
        if tid not in users: bot.send_message(m.chat.id,"Not found"); return
        u=users[tid]; bot.send_message(m.chat.id,f"🔍 {tid} Lv:{level(tid)} Dep:{u['dep']} D:{u['wins']}/{u['loss']} GWR:{u['gw']}/{u['gl']} Ban:{u['ban']}")
        return
    if up.startswith("/BAN"):
        p=t.split()
        if len(p)<2: return
        try: tid=int(p[1])
        except: return
        ensure(tid,f"User{tid}"); users[tid]["ban"]=True; bot.send_message(m.chat.id,f"⛔ Ban {tid}"); return
    if up.startswith("/UNBAN"):
        p=t.split()
        if len(p)<2: return
        try: tid=int(p[1])
        except: return
        if tid in users: users[tid]["ban"]=False; bot.send_message(m.chat.id,f"✅ Unban {tid}"); return
    if up.startswith("/USERS") or (is_cb and not is_st):
        tot=len(users); ban=sum(1 for u in users.values() if u["ban"]); txt=f"👥 {tot} Ban:{ban}\n"
        for uid2,u in list(users.items())[:30]: txt+=f"{uid2} {level(uid2)} D:{u['wins']}/{u['loss']} GWR:{u['gw']}/{u['gl']}\n"
        bot.send_message(m.chat.id,txt); return
    if up.startswith("/STATS") or is_st:
        tot=len(users); td=sum(u["dep"] for u in users.values()); tw=sum(u["wins"] for u in users.values()); tl=sum(u["loss"] for u in users.values()); gw=sum(u["gw"] for u in users.values()); gl=sum(u["gl"] for u in users.values())
        bot.send_message(m.chat.id,f"📊 Users:{tot} Dep:${td} Daily W:{tw} L:{tl} GWR W:{gw} L:{gl}"); return

@bot.message_handler(commands=['start','admin'])
def start_cmd(m):
    uid=m.from_user.id; ensure(uid,m.from_user.username or m.from_user.first_name); daily(uid)
    if uid in bwait: del bwait[uid]
    if users[uid]["bw"]: users[uid]["bw"]=None
    lv=level(uid)
    if lv=="LOCKED" and uid!=OWNER_ID: tx,mk=locked(uid); bot.send_message(m.chat.id,tx,reply_markup=mk); return
    bot.send_message(m.chat.id,f"👋 Welcome {m.from_user.first_name}! {lv} {users[uid]['used']}/{users[uid]['lim'] if lv!='VIP' else '∞'}",reply_markup=menu())

@bot.message_handler(commands=['adduser','such','search','find','ban','unban','users','stats','gwr','broadcast'])
def adm_cmd(m): adm(m)

def run():
    print("V13.2.9 MINI STARTING - FIXED 409")
    try: bot.delete_webhook(drop_pending_updates=True); print("Webhook deleted")
    except Exception as e: print(f"Webhook err {e}")
    while True:
        try:
            print("Polling...")
            bot.infinity_polling(skip_pending=True,timeout=20,long_polling_timeout=20)
        except Exception as e:
            print(f"Crash {e} retry 5s"); time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run,daemon=True).start()
    port=int(os.environ.get("PORT",8080))
    print(f"Flask port {port}")
    app.run(host="0.0.0.0",port=port)
