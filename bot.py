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

REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD"]
OTC=["EUR/USD OTC","GBP/USD OTC","BTC/USD OTC","USD/BRL OTC"]
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
 tid=str(tid)
 u=db.get(tid)
 if not u: return None
 for k,v in [("today",0),("date",str(date.today())),("banned",False),("total",0),("level","none"),("verified",False)]:
  if k not in u: u[k]=v
 if tid==OWNER:
  u["level"]="vip";u["verified"]=True;u["banned"]=False
 if u.get("date")!=str(date.today()):
  u["today"]=0;u["date"]=str(date.today())
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
 u=ensure(tid)
 lim=5
 if lvl=="starter": lim=20
 if lvl=="pro": lim=100
 if lvl=="vip": lim=999999
 return u.get("today",0)>=lim,u.get("today",0),lim

def inc(tid):
 u=ensure(tid)
 if u: u["today"]=u.get("today",0)+1;db[str(tid)]=u;save(db)

@app.route("/")
def home(): return "V3.5 OK",200

@app.route("/pocket_postback")
def pp():
 sec=request.args.get("secret")
 if sec!=SECRET: return "Blocked",403
 sub=request.args.get("subid") or request.args.get("click_id")
 sm=request.args.get("sum","0")
 try:
  amt=float(sm);gid=str(int(float(sub)))
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
 if tid not in db:
  db[tid]={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),"banned":False};save(db)
 ensure(tid);lvl=get_lvl(tid)
 if lvl=="banned": bot.send_message(m.chat.id,"Banned");return
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("GET SIGNAL",callback_data="go"))
 k.add(types.InlineKeyboardButton("Deposit",callback_data="dep"),types.InlineKeyboardButton("My Status",callback_data="bal"))
 k.add(types.InlineKeyboardButton("Register",url=LINK+"?click_id="+tid))
 if tid==OWNER: k.add(types.InlineKeyboardButton("ADMIN",callback_data="admin"))
 bot.send_message(m.chat.id,f"WELCOME V3.5 Level: {lvl}\nLink: {LINK}?click_id={tid}",reply_markup=k)

@bot.message_handler(commands=["admin"])
def admin_cmd(m):
 if str(m.from_user.id)!=OWNER: return
 bot.send_message(m.chat.id,f"ADMIN Users: {len(db)} Verified: {sum(1 for u in db.values() if u.get('verified'))}")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
 tid=str(c.from_user.id);d=c.data;chat_id=c.message.chat.id
 try: bot.delete_message(chat_id,c.message.message_id)
 except: pass
 if d=="admin":
  if tid!=OWNER: return
  bot.send_message(chat_id,f"ADMIN Users: {len(db)}")
  return
 lvl=get_lvl(tid)
 if lvl=="banned": bot.send_message(chat_id,"Banned");return
 if d=="dep":
  k=types.InlineKeyboardMarkup()
  k.add(types.InlineKeyboardButton("Register",url=LINK+"?click_id="+tid))
  bot.send_message(chat_id,f"Deposit:\n{LINK}?click_id={tid}\nMin $20",reply_markup=k);return
 if d=="bal":
  u=ensure(tid);bot.send_message(chat_id,f"STATUS\nLevel: {lvl}\nTotal: ${u.get('total',0)}\nToday: {u.get('today',0)}");return
 if d=="go":
  is_over,cur,lim=check_limit(tid,lvl)
  if is_over: bot.send_message(chat_id,f"Limit {cur}/{lim} reached");return
  pair=random.choice(REAL+OTC);direction=random.choice(["CALL","PUT"]);exp=random.choice(EXP);inc(tid)
  k=types.InlineKeyboardMarkup();k.add(types.InlineKeyboardButton("Next Signal",callback_data="go"))
  bot.send_message(chat_id,f"SIGNAL\nPair: {pair}\nDirection: {direction}\nExp: {exp}\nLevel: {lvl} {cur+1}/{lim}",reply_markup=k);return

if __name__=="__main__":
 port=int(os.environ.get("PORT",8080))
 app.run(host="0.0.0.0",port=port)
