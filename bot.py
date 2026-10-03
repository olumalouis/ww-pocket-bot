import os,json,random
from datetime import date,datetime
from flask import Flask,request
import telebot
from telebot import types

BOT_TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(BOT_TOKEN)
app=Flask(__name__)

LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
FILE="users.json"
OWNER="8188622130"
SECRET=os.getenv("POSTBACK_SECRET","WW12345")

REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","NZD/USD","EUR/AUD","GBP/JPY","BTC/USD","ETH/USD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","BTC/USD OTC","ETH/USD OTC","EUR/GBP OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","USD/PKR OTC","USD/ARS OTC","USD/BDT OTC","USD/TRY OTC","USD/PHP OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC"]

def load():
 if os.path.exists(FILE):
  try:
   with open(FILE) as f:
    return json.load(f)
  except:
   return {}
 return {}

def save(d):
 with open(FILE,"w") as f:
  json.dump(d,f,indent=2)

db=load()

def ensure(tid):
 u=db.get(str(tid))
 if not u:
  return None
 if "today" not in u:
  u["today"]=0
 if "date" not in u:
  u["date"]=str(date.today())
 if "streak" not in u:
  u["streak"]=0
 if "banned" not in u:
  u["banned"]=False
 if "total" not in u:
  u["total"]=0
 if "level" not in u:
  u["level"]="none"
 if "verified" not in u:
  u["verified"]=False
 if "refs" not in u:
  u["refs"]=0
 if u.get("date")!=str(date.today()):
  u["today"]=0
  u["date"]=str(date.today())
 db[str(tid)]=u
 save(db)
 return u

def get_lvl(tid):
 if str(tid)==OWNER:
  return "vip"
 u=db.get(str(tid))
 if not u:
  return None
 ensure(tid)
 if u.get("banned"):
  return "banned"
 if not u.get("verified"):
  return None
 return u.get("level","starter")

def check(tid,lvl):
 u=ensure(tid)
 if not u:
  return False,0,5
 lim=5
 if lvl=="starter":
  lim=20
 if lvl=="pro":
  lim=100
 if lvl=="vip":
  lim=999999
 used=u.get("today",0)
 return used>=lim,used,lim

def inc(tid):
 u=ensure(tid)
 if u:
  u["today"]=u.get("today",0)+1
  db[str(tid)]=u
  save(db)

def gen(pair,exp,lvl):
 cmin=75
 cmax=82
 if lvl=="pro":
  cmin=82
  cmax=89
 if lvl=="vip":
  cmin=89
  cmax=95
 act=random.choice(["BUY","SELL"])
 conf=random.randint(cmin,cmax)
 txt=f"{lvl} {pair} {exp} {act} {conf}%"
 return txt,conf

@app.route("/")
def home():
 return "V3 Active 32 pairs"

@app.route(f"/{BOT_TOKEN}",methods=["POST"])
def wh():
 s=request.get_data().decode("utf-8")
 up=telebot.types.Update.de_json(s)
 bot.process_new_updates([up])
 return ""

@app.route("/pocket_postback")
def pp():
 sec=request.args.get("secret")
 if sec!=SECRET:
  return "Blocked",403
 sub=request.args.get("subid")
 if not sub:
  sub=request.args.get("click_id")
 sm=request.args.get("sum","0")
 try:
  amt=float(sm)
  gid=str(int(float(sub)))
 except:
  return "invalid",400
 u=db.get(gid)
 if not u:
  u={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False}
 tot=u.get("total",0)+amt
 lvl="starter"
 if tot>=100:
  lvl="vip"
 elif tot>=50:
  lvl="pro"
 u["total"]=tot
 u["level"]=lvl
 u["verified"]=True
 db[gid]=u
 save(db)
 return "ok",200

def kb_start(tid):
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("START TRADING",callback_data="go"))
 k.add(types.InlineKeyboardButton("Deposit",callback_data="dep"),types.InlineKeyboardButton("Status",callback_data="bal"))
 k.add(types.InlineKeyboardButton("Win Rate",callback_data="win"),types.InlineKeyboardButton("How to Use",callback_data="how"))
 k.add(types.InlineKeyboardButton("Register",url=f"{LINK}?click_id={tid}"))
 return k

@bot.message_handler(commands=["start"])
def st(m):
 tid=str(m.from_user.id)
 args=m.text.split()
 inv=None
 if len(args)>1:
  inv=args[1].replace("ref_","")
 if tid not in db:
  db[tid]={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False,"inv":inv}
  if inv and inv in db and inv!=tid:
   db[inv]["refs"]=db[inv].get("refs",0)+1
  save(db)
 else:
  ensure(tid)
 u=db[tid]
 lv=u.get("level","none")
 if not u.get("verified") and tid!=OWNER:
  lv="FREE"
 used=u.get("today",0)
 msg=f"WELCOME V3\nFREE 5 $20=20 $50=100 $100=Unlimited\nLevel {lv} Used {used}\n32 pairs\nID {tid}\n{LINK}?click_id={tid}"
 bot.send_message(m.chat.id,msg,reply_markup=kb_start(tid))

@bot.message_handler(commands=["admin"])
def ad(m):
 tid=str(m.from_user.id)
 if tid!=OWNER:
  bot.send_message(m.chat.id,"Owner only")
  return
 tot=len(db)
 bot.send_message(m.chat.id,f"ADMIN V3 Users {tot} Pairs 32")

@bot.message_handler(commands=["balance"])
def bal(m):
 tid=str(m.from_user.id)
 u=ensure(tid)
 if not u:
  return
 lim,used=5,0
 _,used,lim=check(tid,u.get("level","free"))
 bot.send_message(m.chat.id,f"Status {used}/{lim} Total {u.get('total',0)} Level {u.get('level')}")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
 tid=str(c.from_user.id)
 d=c.data
 if d=="go":
  lvl=get_lvl(tid)
  if not lvl:
   bot.send_message(c.message.chat.id,f"FREE 5/day Deposit $20 for 20/day {LINK}?click_id={tid}")
   bot.answer_callback_query(c.id)
   return
  limed,used,lim=check(tid,lvl)
  if limed:
   bot.send_message(c.message.chat.id,f"Limit {used}/{lim} {LINK}?click_id={tid}")
   bot.answer_callback_query(c.id)
   return
  k=types.InlineKeyboardMarkup(row_width=2)
  k.add(types.InlineKeyboardButton("Real 12",callback_data="real_man"),types.InlineKeyboardButton("OTC 20",callback_data="otc_man"))
  bot.send_message(c.message.chat.id,f"Choose Market {lvl} {used}/{lim}",reply_markup=k)
 elif d=="bal":
  tid=str(c.from_user.id)
  u=ensure(tid)
  _,used,lim=check(tid,u.get("level","free"))
  bot.send_message(c.message.chat.id,f"Status {used}/{lim}")
 elif d.startswith("real_") or d.startswith("otc_"):
  parts=d.split("_")
  mtype=parts[0]
  is_otc=mtype=="otc"
  lvl=get_lvl(tid)
  if not lvl:
   lvl="starter"
  tier_pairs=REAL
  if is_otc:
   tier_pairs=OTC
  k=types.InlineKeyboardMarkup(row_width=2)
  for p in tier_pairs[:10]:
   k.add(types.InlineKeyboardButton(p,callback_data=f"p_{p.replace(' ','_')}_{mtype}"))
  bot.send_message(c.message.chat.id,f"Pair {mtype} {len(tier_pairs)}",reply_markup=k)
 elif d.startswith("p_"):
  full=d[2:]
  mtype=full.split("_")[-1]
  pair="_".join(full.split("_")[:-1])
  pair=pair.replace("_"," ")
  if mtype=="otc" and "OTC" not in pair:
   pair+=" OTC"
  k=types.InlineKeyboardMarkup(row_width=3)
  k.add(types.InlineKeyboardButton("1m",callback_data=f"e_{pair.replace(' ','_')}_1m"))
  k.add(types.InlineKeyboardButton("2m",callback_data=f"e_{pair.replace(' ','_')}_2m"))
  k.add(types.InlineKeyboardButton("3m",callback_data=f"e_{pair.replace(' ','_')}_3m"))
  bot.send_message(c.message.chat.id,f"Expiry for {pair}",reply_markup=k)
 elif d.startswith("e_"):
  full=d[2:]
  pp,ex=full.rsplit("_",1)
  pair=pp.replace("_"," ")
  lvl=get_lvl(tid)
  if not lvl:
   lvl="starter"
  _,used,lim=check(tid,lvl)
  if used>=lim:
   bot.send_message(c.message.chat.id,f"Limit {used}/{lim}")
   bot.answer_callback_query(c.id)
   return
  txt,conf=gen(pair,ex,lvl)
  inc(tid)
  bot.send_message(c.message.chat.id,txt)
 bot.answer_callback_query(c.id)

if __name__=="__main__":
 bot.remove_webhook()
 import time
 time.sleep(1)
 URL=os.getenv("RAILWAY_PUBLIC_DOMAIN")
 if not URL:
  URL=os.getenv("WEBHOOK_URL")
 if URL:
  if not URL.startswith("https://"):
   URL="https://"+URL
  full=f"{URL}/{BOT_TOKEN}"
  bot.set_webhook(url=full)
  print(f"Webhook {full}")
 else:
  bot.infinity_polling()
 app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))
