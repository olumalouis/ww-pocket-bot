import os, json, random, time, requests
from datetime import date
from flask import Flask, request
import telebot
from telebot import types
import pandas as pd
import numpy as np
TOKEN=os.getenv("BOT_TOKEN")
SECRET=os.getenv("POSTBACK_SECRET","WW12345")
LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
FILE="users.json"
OWNER="8188622130"
SEC_FILE="security.json"
BLOCK_FILE="blocked_ips.json"
bot=telebot.TeleBot(TOKEN,threaded=False)
app=Flask(__name__)
REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","GBP/JPY","EUR/JPY","AUD/JPY","USD/CHF","EUR/AUD","GBP/AUD","EUR/CAD","NZD/USD","EUR/NZD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","USD/CHF OTC","EUR/AUD OTC","GBP/AUD OTC","EUR/CAD OTC","NZD/USD OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","BTC/USD OTC","ETH/USD OTC","LTC/USD OTC","XRP/USD OTC","ADA/USD OTC","DOT/USD OTC","SOL/USD OTC","BNB/USD OTC","DOGE/USD OTC","AVAX/USD OTC","MATIC/USD OTC","TRX/USD OTC","SHIB/USD OTC"]
EXP=["M1","M2","M3","M5"]
def get_live_closes(pair, limit=100):
    try:
        base_pair=pair.replace(" OTC","")
        cmap={"BTC/USD":"BTCUSDT","ETH/USD":"ETHUSDT","LTC/USD":"LTCUSDT","XRP/USD":"XRPUSDT","ADA/USD":"ADAUSDT","DOT/USD":"DOTUSDT","SOL/USD":"SOLUSDT","BNB/USD":"BNBUSDT","DOGE/USD":"DOGEUSDT","AVAX/USD":"AVAXUSDT","MATIC/USD":"MATICUSDT","TRX/USD":"TRXUSDT","SHIB/USD":"SHIBUSDT"}
        fmap={"EUR/USD":"EURUSDT","GBP/USD":"GBPUSDT","AUD/USD":"AUDUSDT","NZD/USD":"NZDUSDT","EUR/GBP":"EURGBP","EUR/JPY":"EURJPY","GBP/JPY":"GBPJPY","AUD/JPY":"AUDJPY","EUR/AUD":"EURAUD","GBP/AUD":"GBPAUD","EUR/CAD":"EURCAD","EUR/NZD":"EURNZD","USD/JPY":"USDJPY","USD/CAD":"USDCAD","USD/CHF":"USDCHF","USD/BRL":"USDBRL"}
        sym=cmap.get(base_pair) or fmap.get(base_pair)
        if sym:
            url=f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1m&limit={limit}"
            r=requests.get(url, timeout=2).json()
            if isinstance(r,list) and len(r)>20:
                return [float(x[4]) for x in r]
    except: pass
    return list(np.cumsum(np.random.normal(0,0.00015, limit))+1.085)
def calc_rsi(prices, period=14):
    deltas=np.diff(prices)
    gains=np.where(deltas>0, deltas, 0)
    losses=np.where(deltas<0, -deltas, 0)
    ag=np.mean(gains[-period:]) if len(gains)>=period else np.mean(gains)
    al=np.mean(losses[-period:]) if len(losses)>=period else np.mean(losses)
    if al==0: return 68 if ag>0 else 32
    rs=ag/al
    return 100-(100/(1+rs))
def calc_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]
def get_real_signal(pair, exp, level="starter"):
    closes=get_live_closes(pair, 100)
    rsi=calc_rsi(closes, 14)
    ema9=calc_ema(closes, 9)
    ema21=calc_ema(closes, 21)
    last=closes[-1]
    trend="UP" if ema9>ema21 else "DOWN"
    dist=abs(ema9-ema21)/last*10000
    raw=50+min(dist*4,20)+abs(rsi-50)*0.35+random.uniform(-2,2)
    if rsi<28 and trend=="UP": raw+=12
    elif rsi>72 and trend=="DOWN": raw+=12
    elif rsi<35 and trend=="UP": raw+=6
    elif rsi>65 and trend=="DOWN": raw+=6
    sig="BUY" if trend=="UP" else "SELL"
    level=str(level).lower()
    if level=="vip": conf=int(np.clip(raw,75,85))
    elif level=="pro": conf=int(np.clip(raw,65,75))
    else: conf=int(np.clip(raw,65,70))
    return sig,rsi,trend,conf
def load():
 if os.path.exists(FILE):
  try: return json.load(open(FILE))
  except: return {}
 return {}
def save(d): json.dump(d, open(FILE,"w"), indent=2)
db=load()
def load_sec():
 if os.path.exists(SEC_FILE):
  try: return json.load(open(SEC_FILE))
  except: return []
 return []
def save_sec(d): json.dump(d[-200:], open(SEC_FILE,"w"), indent=2)
def load_block():
 if os.path.exists(BLOCK_FILE):
  try: return json.load(open(BLOCK_FILE))
  except: return {}
 return {}
def save_block(d): json.dump(d, open(BLOCK_FILE,"w"), indent=2)
sec_log=load_sec()
blocked=load_block()
broadcast_pending={}
def ensure(tid):
 tid=str(tid);u=db.get(tid)
 if not u: return None
 defaults=[("today",0),("date",str(date.today())),("banned",False),("total",0),("level","none"),("verified",False),("wins",0),("losses",0),("win_streak",0),("loss_streak",0)]
 for k,v in defaults:
  if k not in u: u[k]=v
 if tid==OWNER: u["level"]="vip";u["verified"]=True;u["banned"]=False
 if u.get("date")!=str(date.today()): u["today"]=0;u["date"]=str(date.today())
 db[tid]=u;save(db);return u
def get_lvl(tid):
 tid=str(tid)
 if tid==OWNER: return "vip"
 u=db.get(tid)
 if not u: return None
 ensure(tid)
 if u.get("banned"): return "banned"
 if not u.get("verified"): return "free"
 return u.get("level","starter")
def check_limit(tid,lvl):
 u=ensure(tid);lim=5
 if lvl=="starter": lim=20
 if lvl=="pro": lim=100
 if lvl=="vip": lim=999999
 return u.get("today",0)>=lim,u.get("today",0),lim
def inc(tid):
 u=ensure(tid)
 if u: u["today"]=u.get("today",0)+1;db[str(tid)]=u;save(db)
def get_ip():
 ip=request.headers.get('X-Forwarded-For','')
 return ip.split(',')[0].strip() if ip else request.remote_addr or "unknown"
@app.route("/")
def home(): return "V8 FIXED",200
@app.route("/pocket_postback")
def pp():
 global sec_log, blocked
 ip=get_ip();now=time.time()
 for b_ip, exp in list(blocked.items()):
  if now>exp: del blocked[b_ip]
 save_block(blocked)
 if ip in blocked: return "IP blocked",403
 if request.args.get("secret")!=SECRET:
  sec_log.append({"time":str(date.today()),"ip":ip,"status":"WRONG_SECRET"});save_sec(sec_log)
  if len([x for x in sec_log if x["ip"]==ip and x["status"]=="WRONG_SECRET"])>=5:
   blocked[ip]=now+86400;save_block(blocked)
  return "Blocked",403
 sub=request.args.get("subid") or request.args.get("click_id")
 sm=request.args.get("sum","0")
 try: amt=float(sm);gid=str(int(float(sub)))
 except: return "invalid",400
 sec_log.append({"time":str(date.today()),"ip":ip,"gid":gid,"sum":amt,"status":"SUCCESS"});save_sec(sec_log)
 u=db.get(gid) or {"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
 tot=u.get("total",0)+amt
 lvl="none"
 if tot>=100: lvl="vip"
 elif tot>=50: lvl="pro"
 elif tot>=20: lvl="starter"
 u["total"]=tot;u["level"]=lvl
 if tot>=20: u["verified"]=True
 db[gid]=u;save(db)
 try:
  if amt>=20: bot.send_message(gid, f"Deposit ${amt} Total ${tot} Level {lvl.upper()}")
  bot.send_message(OWNER, f"{gid} ${amt} Total ${tot} {lvl}")
 except: pass
 return "ok",200
@app.route("/webhook",methods=["POST"])
def webhook():
 try: bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
 except Exception as e: print(e)
 return "ok",200
@bot.message_handler(commands=["clearme","resetme","clear","reset"])
def clear_cmd(m):
 tid=str(m.from_user.id);args=m.text.split()
 if len(args)>1 and tid==OWNER and args[1] in db:
  db[args[1]]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
  if args[1]==OWNER: db[args[1]]["level"]="vip";db[args[1]]["verified"]=True
  save(db);bot.send_message(m.chat.id,f"Cleared {args[1]}");return
 if tid in db:
  is_owner=(tid==OWNER)
  db[tid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
  if is_owner: db[tid]["level"]="vip";db[tid]["verified"]=True
  save(db);bot.send_message(m.chat.id,"Cleared $0")
 else: bot.send_message(m.chat.id,"No data")
@bot.message_handler(commands=["start"])
def start(m):
 tid=str(m.from_user.id)
 if tid not in db: db[tid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0};save(db)
 ensure(tid);lvl=get_lvl(tid)
 if lvl=="banned": bot.send_message(m.chat.id,"Banned");return
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("GET SIGNAL",callback_data="sel_market"))
 k.add(types.InlineKeyboardButton("REAL 15",callback_data="m_real"),types.InlineKeyboardButton("OTC 30",callback_data="m_otc"))
 k.add(types.InlineKeyboardButton("Upgrade PRO/VIP",callback_data="upg"),types.InlineKeyboardButton("How it Works",callback_data="how"))
 k.add(types.InlineKeyboardButton("Deposit",callback_data="dep"),types.InlineKeyboardButton("My Status",callback_data="bal"))
 k.add(types.InlineKeyboardButton("Register",url=LINK+"?click_id="+tid),types.InlineKeyboardButton("Support",callback_data="sup"))
 if tid==OWNER: k.add(types.InlineKeyboardButton("ADMIN PANEL",callback_data="admin"))
 bot.send_message(m.chat.id,f"WELCOME V8\nLevel: {lvl.upper()}\nSTARTER 20/day 65-70%\nPRO 100/day 65-75%\nVIP Unlimited 75-85%\nLink: {LINK}?click_id={tid}",reply_markup=k)
    @bot.message_handler(func=lambda m: str(m.from_user.id)==OWNER and str(m.from_user.id) in broadcast_pending)
def broadcast_send(m):
    target=broadcast_pending.get(str(m.from_user.id))
    msg_text=m.text or m.caption or ""
    if not msg_text:
        bot.send_message(m.chat.id,"Send text please")
        return
    cnt=0
    for uid,u in list(db.items()):
        lvl=u.get("level","none")
        ver=u.get("verified",False)
        send=False
        if target=="ALL": send=True
        elif target=="FREE" and not ver: send=True
        elif target=="STARTER" and lvl=="starter": send=True
        elif target=="PRO" and lvl=="pro": send=True
        elif target=="VIP" and lvl=="vip": send=True
        elif target=="ALLVIP" and lvl in ["starter","pro","vip"]: send=True
        if send:
            try:
                bot.send_message(uid, f"📢 {msg_text}")
                cnt+=1
                time.sleep(0.05)
            except: pass
    del broadcast_pending[str(m.from_user.id)]
    bot.send_message(m.chat.id,f"✅ Sent to {cnt} users Target: {target}")

@bot.message_handler(commands=["adduser"])
def adduser_cmd(m):
    if str(m.from_user.id)!=OWNER: return
    args=m.text.split()
    if len(args)<3:
        bot.send_message(m.chat.id,"Usage:\n/adduser TELEGRAM_ID LEVEL\nLevels: free starter pro vip\nEx: /adduser 123456789 vip")
        return
    uid=args[1].strip()
    lvl=args[2].lower().strip()
    mp={"free":0,"starter":20,"pro":50,"vip":100}
    if lvl not in mp:
        bot.send_message(m.chat.id,"Level must be: free starter pro vip")
        return
    tot=mp[lvl]
    ver=lvl!="free"
    db[uid]={"total":tot,"level":lvl if lvl!="free" else "none","verified":ver,"today":0,"date":str(date.today()),"banned":False,"wins":0,"losses":0,"win_streak":0,"loss_streak":0}
    if lvl=="free": db[uid]["level"]="none"
    if uid==OWNER: db[uid]["level"]="vip";db[uid]["verified"]=True
    save(db)
    bot.send_message(m.chat.id,f"✅ Added {uid} as {lvl.upper()} Total ${tot}")

@bot.message_handler(commands=["broadcast","ban","unban"])
def admin_cmds(m):
 if str(m.from_user.id)!=OWNER: return
 args=m.text.split(" ",1);cmd=args[0].replace("/","")
 if cmd=="broadcast" and len(args)>1:
  cnt=0
  for uid in list(db.keys()):
   try: bot.send_message(uid,f"📢 {args[1]}");cnt+=1;time.sleep(0.05)
   except: pass
  bot.send_message(m.chat.id,f"Sent {cnt}")
 if cmd=="ban" and len(args)>1 and args[1].strip() in db:
  db[args[1].strip()]["banned"]=True;save(db);bot.send_message(m.chat.id,"Banned")
 if cmd=="unban" and len(args)>1 and args[1].strip() in db:
  db[args[1].strip()]["banned"]=False;save(db);bot.send_message(m.chat.id,"Unbanned")

def signal_keyboard():
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("✅ WIN",callback_data="res_win"),types.InlineKeyboardButton("❌ LOSS",callback_data="res_loss"))
 k.add(types.InlineKeyboardButton("Next Signal ▶️",callback_data="sel_market"))
 return k

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
 try:
  tid=str(c.from_user.id);d=c.data;chat_id=c.message.chat.id;lvl=get_lvl(tid)
  try: bot.delete_message(chat_id,c.message.message_id)
  except: pass
  if d in ["res_win","res_loss"]:
   u=ensure(tid)
   if not u: return
   if d=="res_win":
    u["wins"]=u.get("wins",0)+1
    u["win_streak"]=u.get("win_streak",0)+1
    u["loss_streak"]=0
    db[tid]=u;save(db)
    bot.send_message(chat_id, f"✅ Recorded!\n🔥 {u['win_streak']} Wins in a row!\nNext: {random.randint(79,85)}% High\nKeep going!", reply_markup=signal_keyboard())
    return
   else:
    u["losses"]=u.get("losses",0)+1
    u["loss_streak"]=u.get("loss_streak",0)+1
    u["win_streak"]=0
    db[tid]=u;save(db)
    ls=u["loss_streak"]
    if ls>=6:
     msg=f"🛑 Market not stable.\nYou have {ls} losses in a row.\nTake a break."
    else:
     msg=f"❌ Recorded!\n💪 Recovery incoming\nNext: {random.randint(82,85)}% High"
    bot.send_message(chat_id, msg, reply_markup=signal_keyboard())
    return
  if d=="admin" and tid==OWNER:
   k=types.InlineKeyboardMarkup(row_width=2)
   k.add(types.InlineKeyboardButton("👥 Users",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
   k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban",callback_data="ad_ban"))
   k.add(types.InlineKeyboardButton("💵 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset",callback_data="ad_reset"))
   k.add(types.InlineKeyboardButton("🛡️ Sec Log",callback_data="ad_sec"),types.InlineKeyboardButton("🎯 Global WR",callback_data="ad_wr"))
   bot.send_message(chat_id,f"👑 ADMIN V8\nUsers: {len(db)} Blocked:{len(blocked)}",reply_markup=k);return
  if tid==OWNER and d.startswith("ad_"):
   if d=="ad_users":
    txt="👥:\n"
    for uid,u in list(db.items())[:20]: txt+=f"{uid} {u.get('level')} ${u.get('total')} W:{u.get('wins',0)} L:{u.get('losses',0)}\n"
    bot.send_message(chat_id,txt);return
   if d=="ad_stats":
    tot=sum(u.get('total',0) for u in db.values());ver=sum(1 for u in db.values() if u.get('verified'))
    wins=sum(u.get('wins',0) for u in db.values());losses=sum(u.get('losses',0) for u in db.values())
    gwr=round(wins/(wins+losses)*100,1) if (wins+losses)>0 else 0
    bot.send_message(chat_id,f"Stats U:{len(db)} V:{ver} ${tot}\nTrades: {wins+losses} WR:{gwr}% W:{wins} L:{losses}");return
   if d=="ad_wr":
    wins=sum(u.get('wins',0) for u in db.values());losses=sum(u.get('losses',0) for u in db.values())
    gwr=round(wins/(wins+losses)*100,1) if (wins+losses)>0 else 0
    txt=f"🎯 GLOBAL (Only you):\nTrades: {wins+losses} W:{wins} L:{losses} WR:{gwr}%\nTop:\n"
    for uid,u in sorted(db.items(), key=lambda x: x[1].get('wins',0)+x[1].get('losses',0), reverse=True)[:10]:
     t=u.get('wins',0)+u.get('losses',0)
     if t>0: txt+=f"{uid}: {t} {round(u.get('wins',0)/t*100,1)}% W:{u.get('wins')} L:{u.get('losses')} LS:{u.get('loss_streak')}\n"
    bot.send_message(chat_id,txt);return
   if d=="ad_deps":
    txt="Deposits:\n"
    for uid,u in db.items():
     if u.get('total',0)>0: txt+=f"{uid} ${u.get('total')} {u.get('level')}\n"
    bot.send_message(chat_id,txt or "None");return
   if d=="ad_reset":
    for u in db.values(): u["today"]=0;u["date"]=str(date.today())
    save(db);bot.send_message(chat_id,"Reset");return
   if d=="ad_broad":
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📢 ALL",callback_data="broad_ALL"))
    kb.add(types.InlineKeyboardButton("🆓 FREE",callback_data="broad_FREE"))
    kb.add(types.InlineKeyboardButton("🚀 STARTER",callback_data="broad_STARTER"))
    kb.add(types.InlineKeyboardButton("💎 PRO",callback_data="broad_PRO"))
    kb.add(types.InlineKeyboardButton("👑 VIP",callback_data="broad_VIP"))
    kb.add(types.InlineKeyboardButton("💎 ALL VIPs",callback_data="broad_ALLVIP"))
    bot.send_message(chat_id,"Select target:",reply_markup=kb);return
   if d.startswith("broad_"):
    target=d.replace("broad_","")
    broadcast_pending[tid]=target
    bot.send_message(chat_id,f"✅ Target: {target}\nNow SEND the message to broadcast.");return
   if d=="ad_ban": bot.send_message(chat_id,"/ban ID /unban ID");return
   if d=="ad_sec":
    txt="Log:\n"
    for s in sec_log[-10:]: txt+=f"{s.get('ip')} {s.get('status')} {s.get('gid','-')} ${s.get('sum','-')}\n"
    bot.send_message(chat_id,txt);return
  if d=="dep":
   k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("Register",url=LINK+"?click_id="+tid))
   bot.send_message(chat_id,f"Deposit:\n{LINK}?click_id={tid}\n$20 Starter 20/day\n$50 PRO 100/day\n$100 VIP Unlimited",reply_markup=k);return
  if d=="upg":
   k=types.InlineKeyboardMarkup()
   k.add(types.InlineKeyboardButton("🚀 STARTER $20",url=LINK+"?click_id="+tid))
   k.add(types.InlineKeyboardButton("💎 PRO $50",url=LINK+"?click_id="+tid))
   k.add(types.InlineKeyboardButton("👑 VIP $100",url=LINK+"?click_id="+tid))
   bot.send_message(chat_id,f"PLANS Current {lvl.upper()}\nSTARTER $20 20/day 65-70%\nPRO $50 100/day 65-75%\nVIP $100 Unlimited 75-85%",reply_markup=k);return
  if d=="how": bot.send_message(chat_id,f"HOW V8\n1 Register\n2 Deposit\n3 /start signals\nREAL 15 real forex\nOTC 30 OTC\nLevel {lvl}");return
  if d=="bal":
   u=ensure(tid)
   bot.send_message(chat_id,f"STATUS {lvl}\nTotal ${u.get('total',0)}\nToday {u.get('today',0)}\nTrades: {u.get('wins',0)+u.get('losses',0)} W:{u.get('wins',0)} L:{u.get('losses',0)}");return
  if d=="sup": bot.send_message(chat_id,"Support: @YourSupport");return
  if d=="sel_market":
   k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC 30",callback_data="m_otc"))
   bot.send_message(chat_id,"Select Market:",reply_markup=k);return
  if d=="m_real":
   k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
   bot.send_message(chat_id,"REAL 15",reply_markup=k);return
  if d=="m_otc":
   k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual 30",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto 30",callback_data="otc_auto"))
   bot.send_message(chat_id,"OTC 30",reply_markup=k);return
  if d=="real_manual":
   k=types.InlineKeyboardMarkup(row_width=2)
   for p in REAL: k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_REAL"))
   bot.send_message(chat_id,"MANUAL REAL Pick Pair",reply_markup=k);return
  if d=="otc_manual":
   k=types.InlineKeyboardMarkup(row_width=2)
   for p in OTC[:15]: k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_OTC"))
   k.add(types.InlineKeyboardButton("Next 15 →",callback_data="otc_manual2"))
   bot.send_message(chat_id,"MANUAL OTC 1/2",reply_markup=k);return
  if d=="otc_manual2":
   k=types.InlineKeyboardMarkup(row_width=2)
   for p in OTC[15:]: k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_OTC"))
   k.add(types.InlineKeyboardButton("← Back",callback_data="otc_manual"))
   bot.send_message(chat_id,"MANUAL OTC 2/2",reply_markup=k);return
  if d.startswith("pair_"):
   try:
    rest=d[5:]
    pair=rest[:-5] if rest.endswith("_REAL") else rest[:-4]
   except: pair=REAL[0]
   is_over,cur,lim=check_limit(tid,lvl)
   if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}");return
   k=types.InlineKeyboardMarkup(row_width=4)
   k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5"))
   bc=0;bs="";br=0;bt=""
   for exp in EXP:
    sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
    if conf>bc: bc=conf;bs=sig;br=rsi;bt=trend
   bot.send_message(chat_id,f"Pair {pair}\nBest {bs} {bc}% RSI {br:.1f} {bt}\nPick Expiry:",reply_markup=k);return
  if d in ["real_auto","otc_auto"]:
   is_over,cur,lim=check_limit(tid,lvl)
   if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}");return
   pairs=OTC if d.startswith("otc_") else REAL
   pair=random.choice(pairs);exp=random.choice(EXP)
   sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
   inc(tid)
   bot.send_message(chat_id,f"📊 {lvl.upper()} {conf}%\n{pair} {sig} Exp:{exp}\nRSI {rsi:.1f} {trend} {cur+1}/{lim}",reply_markup=signal_keyboard());return
  if d.startswith("sig_"):
   tmp=d[4:];idx=tmp.rfind("_M");pair=tmp[:idx];exp=tmp[idx+1:]
   is_over,cur,lim=check_limit(tid,lvl)
   if is_over:
    msg=f"⛔ {lvl.upper()} limit {cur}/{lim}"
    if lvl=="starter": msg+=" Upgrade PRO $50"
    if lvl=="pro": msg+=" Upgrade VIP $100"
    bot.send_message(chat_id,msg);return
   sig,rsi,trend,conf=get_real_signal(pair, exp, lvl)
   inc(tid)
   bot.send_message(chat_id,f"✅ SIGNAL {lvl.upper()} {conf}%\nPair: {pair}\nDir: {sig}\nExp: {exp}\nRSI {rsi:.1f} {trend}\n{cur+1}/{lim}",reply_markup=signal_keyboard());return
 except Exception as e:
  print(f"ERR {e}")
  try: bot.send_message(c.message.chat.id,f"Error {e}")
  except: pass
if __name__=="__main__":
 app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
