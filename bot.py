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
# 15 REAL PAIRS
REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","GBP/JPY","EUR/JPY","AUD/JPY","USD/CHF","EUR/AUD","GBP/AUD","EUR/CAD","NZD/USD","EUR/NZD"]
# 30 OTC PAIRS
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
def home(): return "V4.2 15 REAL 30 OTC BUY SELL PAIR SELECT OK",200
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
 if tid not in db: db[tid]={"total":0,"level":"none","verified":False,"today":0,"date":str
