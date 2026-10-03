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
REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","GBP/JPY","EUR/JPY","AUD/JPY","USD/CHF","EUR/AUD","GBP/AUD","EUR/CAD","NZD/USD","EUR/NZD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","USD/CHF OTC","EUR/AUD OTC","GBP/AUD OTC","EUR/CAD OTC","NZD/USD OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","BTC/USD OTC","ETH/USD OTC","LTC/USD OTC","XRP/USD OTC","ADA/USD OTC","DOT/USD OTC","SOL/USD OTC","BNB/USD OTC","DOGE/USD OTC","AVAX/USD OTC","MATIC/USD OTC","TRX/USD OTC","SHIB/USD OTC"]
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
def home(): return "V4.4 CLEARME OK",200
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
 try:
  if amt>=20:
   bot.send_message(gid, f"🎉 Deposit Confirmed!\n\n💰 Amount: ${amt}\n💵 Total: ${tot}\n⭐ Level: {lvl.upper()}\n\n✅ You are now UNLOCKED!\n{'20 signals/day' if lvl=='starter' else '100 signals/day' if lvl=='pro' else 'UNLIMITED signals'}\n\nSend /start to get signals!")
  bot.send_message(OWNER, f"💰 NEW DEPOSIT!\nUser: {gid}\nAmount: ${amt}\nTotal: ${tot}\nLevel: {lvl}")
 except Exception as e:
  print(f"Notify error: {e}")
 return "ok",200
@app.route("/webhook",methods=["POST"])
def webhook():
 js=request.get_data().decode('utf-8')
 up=telebot.types.Update.de_json(js)
 bot.process_new_updates([up])
 return "ok",200

# --- NEW COMMANDS: /clearme /resetme /clear ---
@bot.message_handler(commands=["clearme","resetme","clear","reset"])
def clear_cmd(m):
 tid=str(m.from_user.id)
 args=m.text.split()
 # /clear USER_ID for owner to clear others
 if len(args)>1 and tid==OWNER:
  target=args[1]
  if target in db:
   db[target]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False}
   if target==OWNER:
    db[target]["level"]="vip";db[target]["verified"]=True
   save(db)
   bot.send_message(m.chat.id,f"✅ Cleared {target} -> $0")
  else:
   bot.send_message(m.chat.id,f"User {target} not found")
  return
 # self clear
 if tid in db:
  is_owner = (tid==OWNER)
  db[tid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False}
  if is_owner:
   db[tid]["level"]="vip";db[tid]["verified"]=True
  save(db)
  bot.send_message(m.chat.id,f"✅ Your data cleared!\nTotal: $0\nLevel: {'vip (owner)' if is_owner else 'none (free)'}\n\nSend /start again")
 else:
  bot.send_message(m.chat.id,"You have no data")

@bot.message_handler(commands=["start"])
def start(m):
 tid=str(m.from_user.id)
 if tid not in db: db[tid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False};save(db)
 ensure(tid);lvl=get_lvl(tid)
 if lvl=="banned": bot.send_message(m.chat.id,"Banned");return
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("📊 GET SIGNAL",callback_data="sel_market"))
 k.add(types.InlineKeyboardButton("💹 REAL Market (15)",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC Market (30)",callback_data="m_otc"))
 k.add(types.InlineKeyboardButton("✋ Manual Mode",callback_data="mode_manual"),types.InlineKeyboardButton("🤖 Auto Mode",callback_data="mode_auto"))
 k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("📈 My Status",callback_data="bal"))
 k.add(types.InlineKeyboardButton("🔗 Register",url=LINK+"?click_id="+tid),types.InlineKeyboardButton("📞 Support",callback_data="sup"))
 if tid==OWNER: k.add(types.InlineKeyboardButton("👑 ADMIN PANEL",callback_data="admin"))
 bot.send_message(m.chat.id,f"WELCOME V4.4\nLevel: {lvl}\nREAL: 15 | OTC: 30\n/clearme to reset test\nLink: {LINK}?click_id={tid}",reply_markup=k)

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
  k.add(types.InlineKeyboardButton("💹 REAL 15",callback_data="m_real"),types.InlineKeyboardButton("🔶 OTC 30",callback_data="m_otc"))
  bot.send_message(chat_id,"Select Market:",reply_markup=k);return
 if d=="m_real":
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual - Pick Pair",callback_data="real_manual"),types.InlineKeyboardButton("🤖 Auto",callback_data="real_auto"))
  bot.send_message(chat_id,"REAL Market (15 pairs)\nManual = You pick pair + BUY/SELL",reply_markup=k);return
 if d=="m_otc":
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("✋ Manual - Pick Pair (30)",callback_data="otc_manual"),types.InlineKeyboardButton("🤖 Auto (30)",callback_data="otc_auto"))
  bot.send_message(chat_id,"OTC Market (30 pairs)\nManual = You pick pair + BUY/SELL",reply_markup=k);return
 if d=="mode_manual":
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("💹 REAL Manual 15",callback_data="real_manual"),types.InlineKeyboardButton("🔶 OTC Manual 30",callback_data="otc_manual"))
  bot.send_message(chat_id,"Manual Mode - Choose market then pair:",reply_markup=k);return
 if d=="mode_auto":
  is_over,cur,lim=check_limit(tid,lvl)
  if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}");return
  pair=random.choice(REAL+OTC);direction=random.choice(["BUY 🟢","SELL 🔴"]);exp=random.choice(EXP);inc(tid)
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("Next REAL",callback_data="real_auto"),types.InlineKeyboardButton("Next OTC",callback_data="otc_auto"))
  bot.send_message(chat_id,f"🤖 AUTO\nPair: {pair}\nSignal: {direction}\nExp: {exp}\n{cur+1}/{lim}",reply_markup=k);return
 if d=="real_manual":
  k=types.InlineKeyboardMarkup(row_width=2)
  for p in REAL:
   k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_REAL"))
  bot.send_message(chat_id,"✋ MANUAL REAL (15)\nStep 1/2: SELECT PAIR",reply_markup=k);return
 if d=="otc_manual":
  k=types.InlineKeyboardMarkup(row_width=2)
  for p in OTC[:15]:
   k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_OTC"))
  k.add(types.InlineKeyboardButton("Next 15 →",callback_data="otc_manual2"))
  bot.send_message(chat_id,"✋ MANUAL OTC (1/2) - 30 pairs\nStep 1/2: SELECT PAIR",reply_markup=k);return
 if d=="otc_manual2":
  k=types.InlineKeyboardMarkup(row_width=2)
  for p in OTC[15:]:
   k.add(types.InlineKeyboardButton(p,callback_data=f"pair_{p}_OTC"))
  k.add(types.InlineKeyboardButton("← Back",callback_data="otc_manual"))
  bot.send_message(chat_id,"✋ MANUAL OTC (2/2) - 30 pairs\nStep 1/2: SELECT PAIR",reply_markup=k);return
 if d.startswith("pair_"):
  try:
   rest=d[5:]
   if rest.endswith("_REAL"): pair=rest[:-5]
   else: pair=rest[:-4]
  except: pair=REAL[0]
  is_over,cur,lim=check_limit(tid,lvl)
  if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}");return
  k=types.InlineKeyboardMarkup(row_width=4)
  k.add(types.InlineKeyboardButton("M1 BUY 🟢",callback_data=f"sig_{pair}_M1_BUY"),types.InlineKeyboardButton("M2 BUY 🟢",callback_data=f"sig_{pair}_M2_BUY"),types.InlineKeyboardButton("M3 BUY 🟢",callback_data=f"sig_{pair}_M3_BUY"),types.InlineKeyboardButton("M5 BUY 🟢",callback_data=f"sig_{pair}_M5_BUY"))
  k.add(types.InlineKeyboardButton("M1 SELL 🔴",callback_data=f"sig_{pair}_M1_SELL"),types.InlineKeyboardButton("M2 SELL 🔴",callback_data=f"sig_{pair}_M2_SELL"),types.InlineKeyboardButton("M3 SELL 🔴",callback_data=f"sig_{pair}_M3_SELL"),types.InlineKeyboardButton("M5 SELL 🔴",callback_data=f"sig_{pair}_M5_SELL"))
  bot.send_message(chat_id,f"✋ MANUAL\nPair: {pair}\nStep 2/2: SELECT EXPIRY + BUY/SELL",reply_markup=k);return
 if d in ["real_auto","otc_auto"]:
  is_over,cur,lim=check_limit(tid,lvl)
  if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim}");return
  is_otc=d.startswith("otc_");pair=random.choice(OTC if is_otc else REAL);direction=random.choice(["BUY 🟢","SELL 🔴"]);exp=random.choice(EXP);inc(tid)
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("Next REAL",callback_data="real_auto"),types.InlineKeyboardButton("Next OTC",callback_data="otc_auto"))
  bot.send_message(chat_id,f"📊 SIGNAL\nMarket: {'OTC' if is_otc else 'REAL'}\nPair: {pair}\nSignal: {direction}\nExp: {exp}\nLevel: {lvl} {cur+1}/{lim}",reply_markup=k);return
 if d.startswith("sig_"):
  try:
   parts=d.rsplit("_",2)
   pair=parts[0][4:]
   exp=parts[1]
   dirct=parts[2]
  except: pair="EUR/USD";exp="M1";dirct="BUY"
  is_over,cur,lim=check_limit(tid,lvl)
  if not is_over: inc(tid)
  emoji="🟢" if "BUY" in dirct else "🔴"
  k=types.InlineKeyboardMarkup(row_width=2);k.add(types.InlineKeyboardButton("Next REAL Manual",callback_data="real_manual"),types.InlineKeyboardButton("Next OTC Manual",callback_data="otc_manual"))
  bot.send_message(chat_id,f"📊 MANUAL SIGNAL\nPair: {pair}\nSignal: {dirct} {emoji}\nExp: {exp}\nLevel: {lvl}",reply_markup=k);return

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
