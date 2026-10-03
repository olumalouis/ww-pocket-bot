import os, json, random
from datetime import date
from flask import Flask, request
import telebot
from telebot import types
TOKEN=os.getenv("BOT_TOKEN")
SECRET=os.getenv("POSTBACK_SECRET","WW12345")
LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
FILE="users.json"
OWNER="8188622130"
bot=telebot.TeleBot(TOKEN,threaded=False)
app=Flask(__name__)
REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","GBP/JPY"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","USD/CHF OTC","EUR/AUD OTC","GBP/AUD OTC","EUR/CAD OTC","NZD/USD OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","BTC/USD OTC","ETH/USD OTC","LTC/USD OTC"]
EXP=["M1","M2","M3","M5"]
def load():
 if os.path.exists(FILE):
  try:
   with open(FILE) as f: return json.load(f)
  except: return {}
 return {}
def save(d):
 with open(FILE,"w") as f: json.dump(d,f,indent=2)
db=load()
def ensure(tid):
 tid=str(tid);u=db.get(tid)
 if not u: return None
 for k,v in [("today",0),("date",str(date.today())),("banned",False),("total",0),("level","none"),("verified",False)]:
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
@app.route("/")
def home(): return "V3.8 FULL 20 OTC OK",200
@app.route("/pocket_postback")
def pp():
 sec=request.args.get("secret")
 if sec!=SECRET: return "Blocked",403
 sub=request.args.get("subid") or request.args.get("click_id")
 sm=request.args.get("sum","0")
 try: amt=float(sm);gid=str(int(float(sub)))
 except: return "invalid",400
 u=db.get(gid)
 if not u: u={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False}
 tot=u.get("total",0)+amt
 lvl="none"
 if tot>=100: lvl="vip"
 elif tot>=50: lvl="pro"
 elif tot>=20: lvl="starter"
 u["total"]=tot;u["level"]=lvl
 if tot>=20: u["verified"]=True
 db[gid]=u;save(db)
 return "ok",200
@app.route("/webhook",methods=["POST"])
def webhook():
 js=request.get_data().decode('utf-8')
 up=telebot.types.Update.de_json(js)
 bot.process_new_updates([up])
 return "ok",200
@bot.message_handler(commands=["start"])
def start(m):
 tid=str(m.from_user.id)
 if tid not in db: db[tid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False};save(db)
 ensure(tid);lvl=get_lvl(tid)
 if lvl=="banned": bot.send_message(m.chat.id,"Banned");return
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("📊 GET SIGNAL",callback_data="sel_market"))
 k.add(types.InlineKeyboardButton("💹 REAL Market",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC Market (20)",callback_data="m_otc"))
 k.add(types.InlineKeyboardButton("✋ Manual Mode",callback_data="mode_manual"),types.InlineKeyboardButton("🤖 Auto Mode",callback_data="mode_auto"))
 k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("📈 My Status",callback_data="bal"))
 k.add(types.InlineKeyboardButton("🔗 Register",url=LINK+"?click_id="+tid),types.InlineKeyboardButton("📞 Support",callback_data="sup"))
 if tid==OWNER: k.add(types.InlineKeyboardButton("👑 ADMIN PANEL",callback_data="admin"))
 bot.send_message(m.chat.id,f"WELCOME V3.8 FULL\nLevel: {lvl}\nOTC Pairs: 20\nREAL: 7\n\nUser Buttons: 8\nAdmin: 6\nLink: {LINK}?click_id={tid}",reply_markup=k)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
 tid=str(c.from_user.id);d=c.data;chat_id=c.message.chat.id
 try: bot.delete_message(chat_id,c.message.message_id)
 except: pass
 lvl=get_lvl(tid)
 if d=="admin" and tid==OWNER:
  k=types.InlineKeyboardMarkup(row_width=2)
  k.add(types.InlineKeyboardButton("👥 Users List",callback_data="ad_users"),types.InlineKeyboardButton("📊 Stats",callback_data="ad_stats"))
  k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="ad_broad"),types.InlineKeyboardButton("🚫 Ban User",callback_data="ad_ban"))
  k.add(types.InlineKeyboardButton("💵 Deposits",callback_data="ad_deps"),types.InlineKeyboardButton("🔄 Reset Daily",callback_data="ad_reset"))
  bot.send_message(chat_id,f"👑 ADMIN PANEL - 6 Buttons\nUsers: {len(db)}\nSelect:",reply_markup=k);return
 if tid==OWNER:
  if d=="ad_users":
   txt="👥 USERS:\n"
   for i,(uid,u) in enumerate(list(db.items())[:20]): txt+=f"{i+1}. {uid} {u.get('level')} ${u.get('total',0)}\n"
   bot.send_message(chat_id,txt);return
  if d=="ad_stats":
   tot=sum(u.get('total',0) for u in db.values());ver=sum(1 for u in db.values() if u.get('verified'))
   bot.send_message(chat_id,f"📊 STATS\nUsers: {len(db)}\nVerified: {ver}\nTotal Deposits: ${tot}\nFree: {sum(1 for u in db.values() if u.get('level')=='none')}");return
  if d=="ad_deps":
   txt="💵 DEPOSITS:\n"
   for uid,u in db.items():
    if u.get('total',0)>0: txt+=f"{uid}: ${u.get('total')} {u.get('level')}\n"
   bot.send_message(chat_id,txt if len(txt)>15 else "No deposits yet");return
  if d=="ad_reset":
   for u in db.values(): u["today"]=0;u["date"]=str(date.today())
   save(db);bot.send_message(chat_id,"✅ Daily limits reset");return
  if d=="ad_broad": bot.send_message(chat_id,"Send /broadcast YourMessage to broadcast");return
  if d=="ad_ban": bot.send_message(chat_id,"Send /ban USER_ID to ban\n/unban USER_ID");return
 if d=="dep":
  k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("Register",url=LINK+"?click_id="+tid))
  bot.send_message(chat_id,f"💰 Deposit:\n{LINK}?click_id={tid}\nMin $20 Starter\n$50 Pro\n$100 VIP",reply_markup=k);return
 if d=="bal":
  u=ensure(tid);bot.send_message(chat_id,f"📈 STATUS\nLevel: {lvl}\nTotal: ${u.get('total',0)}\nToday: {u.get('today',0)}\nVerified: {u.get('verified')}\nBanned: {u.get('banned')}");return
 if d=="sup": bot.send_message(chat_id,"Support: Contact @YourSupport");return
 if d=="sel_market":
  k=types.InlineKeyboardMarkup(row_width=2)
  k.add(types.InlineKeyboardButton("💹 REAL",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC 20",callback_data="m_otc"))
  bot.send_message(chat_id,"Select Market:",reply_markup=k);return
 if d in ["m_real","mode_manual_real","mode_auto_real"]: d="real_manual" if "manual" in d else "real_auto" if d!="m_real" else d
 if d=="m_real":
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
  bot.send_message(chat_id,"REAL Market\nChoose mode:",reply_markup=k);return
 if d=="m_otc":
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="otc_auto"))
  bot.send_message(chat_id,"OTC Market (20 pairs)\nChoose mode:",reply_markup=k);return
 if d=="mode_manual":
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL Manual",callback_data="real_manual"),types.InlineKeyboardButton("🔶 OTC Manual",callback_data="otc_manual"))
  bot.send_message(chat_id,"Manual Mode - Choose market:",reply_markup=k);return
 if d=="mode_auto":
  is_over,cur,lim=check_limit(tid,lvl)
  if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}");return
  pair=random.choice(REAL+OTC);direction=random.choice(["CALL","PUT"]);exp=random.choice(EXP);inc(tid)
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("Next REAL",callback_data="real_auto"),types.InlineKeyboardButton("Next OTC",callback_data="otc_auto"))
  bot.send_message(chat_id,f"🤖 AUTO\nPair: {pair}\nDirection: {direction}\nExp: {exp}\n{cur+1}/{lim}",reply_markup=k);return
 if d.startswith("real_") or d.startswith("otc_"):
  is_over,cur,lim=check_limit(tid,lvl)
  if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}");return
  is_otc=d.startswith("otc_");is_manual="manual" in d
  pair=random.choice(OTC if is_otc else REAL);direction=random.choice(["CALL","PUT"]);inc(tid)
  if is_manual:
   k=types.InlineKeyboardMarkup(row_width=4)
   k.add(types.InlineKeyboardButton("M1",callback_data=f"sig_{pair}_M1_{direction}"),types.InlineKeyboardButton("M2",callback_data=f"sig_{pair}_M2_{direction}"),types.InlineKeyboardButton("M3",callback_data=f"sig_{pair}_M3_{direction}"),types.InlineKeyboardButton("M5",callback_data=f"sig_{pair}_M5_{direction}"))
   bot.send_message(chat_id,f"✋ MANUAL\nMarket: {'OTC' if is_otc else 'REAL'}\nPair: {pair}\nDir: {direction}\nChoose expiry:",reply_markup=k)
  else:
   exp=random.choice(EXP)
   k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("Next REAL",callback_data="real_auto"),types.InlineKeyboardButton("Next OTC",callback_data="otc_auto"))
   bot.send_message(chat_id,f"📊 SIGNAL\nMarket: {'OTC' if is_otc else 'REAL'}\nPair: {pair}\nDir: {direction}\nExp: {exp}\nLevel: {lvl} {cur+1}/{lim}",reply_markup=k)
  return
 if d.startswith("sig_"):
  try: _,pair,exp,dirct=d.split("_",3)
  except: pair="EUR/USD";exp="M1";dirct="CALL"
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("Next REAL",callback_data="real_auto"),types.InlineKeyboardButton("Next OTC",callback_data="otc_auto"))
  bot.send_message(chat_id,f"📊 MANUAL SIGNAL\nPair: {pair}\nDir: {dirct}\nExp: {exp}",reply_markup=k);return

@bot.message_handler(commands=["broadcast"])
def bcast(m):
 if str(m.from_user.id)!=OWNER: return
 txt=m.text.replace("/broadcast","").strip()
 if not txt: bot.send_message(m.chat.id,"Usage: /broadcast message");return
 cnt=0
 for uid in db:
  try: bot.send_message(uid,txt);cnt+=1
  except: pass
 bot.send_message(m.chat.id,f"Broadcast sent to {cnt}")

@bot.message_handler(commands=["ban","unban"])
def ban(m):
 if str(m.from_user.id)!=OWNER: return
 parts=m.text.split()
 if len(parts)<2: return
 uid=parts[1]
 if uid in db:
  db[uid]["banned"]=m.text.startswith("/ban");save(db)
  bot.send_message(m.chat.id,f"{'Banned' if db[uid]['banned'] else 'Unbanned'} {uid}")

if __name__=="__main__":
 port=int(os.environ.get("PORT",8080))
 app.run(host="0.0.0.0",port=port)
