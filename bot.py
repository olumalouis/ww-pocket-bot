import os,json,random
from datetime import date,datetime
from flask import Flask,request
import telebot
from telebot import types

TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)
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
 act=random.choice(["BUY UP","SELL DOWN"])
 conf=random.randint(cmin,cmax)
 mt="OTC" if "OTC" in pair else "REAL"
 txt=f"🎯 {lvl.upper()} SIGNAL\nPair {pair}\nMarket {mt}\nExpiry {exp}\nAction {act}\nConf {conf}%\nWin {conf}%\nUTC {datetime.utcnow().strftime('%H:%M')}"
 return txt,conf

@app.route("/")
def home():
 return "V3 Full 32"

@app.route(f"/{TOKEN}",methods=["POST"])
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
 try:
  bot.send_message(int(gid),f"✅ Deposit ${amt} Total ${tot} Level {lvl.upper()} Limit checked /balance")
 except:
  pass
 return "ok",200

def kb_start(tid):
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("🚀 START TRADING",callback_data="go"))
 k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("📊 My Status",callback_data="bal"))
 k.add(types.InlineKeyboardButton("📈 Win Rate",callback_data="win"),types.InlineKeyboardButton("🎓 How to Use",callback_data="how"))
 k.add(types.InlineKeyboardButton("👥 Referral",callback_data="ref"),types.InlineKeyboardButton("💬 Support",callback_data="sup"))
 k.add(types.InlineKeyboardButton("📝 Register",url=f"{LINK}?click_id={tid}"))
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
 lv=u.get("level","none").upper()
 if not u.get("verified") and tid!=OWNER:
  lv="FREE"
 used=u.get("today",0)
 lim_txt="5"
 if lv=="STARTER":
  lim_txt="20"
 if lv=="PRO":
  lim_txt="100"
 if lv=="VIP" or tid==OWNER:
  lim_txt="♾️"
 msg=f"👋 WELCOME V3 32 PAIRS\nFREE 5 $20=20 $50=100 $100=♾️\nLevel {lv} Used {used}/{lim_txt}\nReal 12 OTC 20\nID {tid}\n{LINK}?click_id={tid}"
 if tid==OWNER:
  msg=f"👑 OWNER VIP\n{msg}\n/admin"
 bot.send_message(m.chat.id,msg,reply_markup=kb_start(tid))

@bot.message_handler(commands=["admin"])
def ad(m):
 tid=str(m.from_user.id)
 if tid!=OWNER:
  bot.send_message(m.chat.id,"Owner only")
  return
 tot=len(db)
 vip=len([x for x in db.values() if x.get("level")=="vip"])
 pro=len([x for x in db.values() if x.get("level")=="pro"])
 st=len([x for x in db.values() if x.get("level")=="starter"])
 free=tot-vip-pro-st
 dep=sum([x.get("total",0) for x in db.values()])
 today=sum([x.get("today",0) for x in db.values() if x.get("date")==str(date.today())])
 k=types.InlineKeyboardMarkup(row_width=2)
 k.add(types.InlineKeyboardButton("Add VIP",callback_data="av"),types.InlineKeyboardButton("Rem VIP",callback_data="rv"))
 k.add(types.InlineKeyboardButton("Ban",callback_data="ban"),types.InlineKeyboardButton("Stats",callback_data="stats"))
 msg=f"ADMIN V3\nUsers {tot}\nVIP {vip} PRO {pro} STARTER {st} FREE {free}\nDeposits ${dep}\nSignals Today {today}\nPairs 32"
 bot.send_message(m.chat.id,msg,reply_markup=k)

@bot.message_handler(commands=["balance","winrate","addvip","remvip","ban"])
def cmds(m):
 tid=str(m.from_user.id)
 txt=m.text
 if txt.startswith("/balance"):
  u=ensure(tid)
  _,used,lim=check(tid,u.get("level","free"))
  if tid==OWNER:
   lim="♾️"
  bot.send_message(m.chat.id,f"Status {used}/{lim} Total ${u.get('total',0)} Level {u.get('level')} Streak {u.get('streak')} Ref {u.get('refs')}")
  return
 if txt.startswith("/winrate"):
  bot.send_message(m.chat.id,"Win Rate 32 pairs\nEUR/USD OTC 88%\nGBP/USD OTC 86%\nBTC OTC 84%\nSTARTER 75-82 PRO 82-89 VIP 89-95")
  return
 if txt.startswith("/addvip") and tid==OWNER:
  try:
   p=txt.split()
   t=p[1]
   u=db.get(t,{"total":100,"level":"vip","verified":True,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False})
   u["total"]=100
   u["level"]="vip"
   u["verified"]=True
   u["banned"]=False
   db[t]=u
   save(db)
   bot.send_message(m.chat.id,f"VIP added {t}")
  except:
   bot.send_message(m.chat.id,"Use /addvip ID")
  return
 if txt.startswith("/remvip") and tid==OWNER:
  try:
   p=txt.split()
   t=p[1]
   if t in db:
    db[t]["level"]="none"
    db[t]["verified"]=False
    save(db)
    bot.send_message(m.chat.id,f"Removed {t}")
  except:
   bot.send_message(m.chat.id,"Use /remvip ID")
  return
 if txt.startswith("/ban") and tid==OWNER:
  try:
   p=txt.split()
   t=p[1]
   if t in db:
    db[t]["banned"]=not db[t].get("banned",False)
    save(db)
    bot.send_message(m.chat.id,f"Ban {t} {db[t]['banned']}")
  except:
   bot.send_message(m.chat.id,"Use /ban ID")
  return

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
 tid=str(c.from_user.id)
 d=c.data
 lvl=get_lvl(tid)
 if d=="go":
  if not lvl:
   # FREEMIUM LOCK 40% chance
   if random.random()<0.4:
    rc=random.randint(84,92)
    pr=random.choice(OTC[:5])
    k=types.InlineKeyboardMarkup()
    k.add(types.InlineKeyboardButton("Unlock $20",url=f"{LINK}?click_id={tid}"))
    bot.send_message(c.message.chat.id,f"🔒 VIP {rc}% LOCKED\nPair {pr}\nReal {rc}% You see 65% blurred\n$20=20 $50=100 $100=♾️\n{LINK}?click_id={tid}",reply_markup=k)
    inc(tid)
    bot.answer_callback_query(c.id)
    return
   bot.send_message(c.message.chat.id,f"FREE teaser 5/day Deposit $20 for 20/day {LINK}?click_id={tid}")
   inc(tid)
   bot.answer_callback_query(c.id)
   return
  limed,used,lim=check(tid,lvl)
  if limed:
   bot.send_message(c.message.chat.id,f"Limit {used}/{lim} Upgrade {LINK}?click_id={tid}")
   bot.answer_callback_query(c.id)
   return
  # WARNING ONLY after 4
  u=ensure(tid)
  if u.get("streak",0)>=4:
   k=types.InlineKeyboardMarkup(row_width=2)
   k.add(types.InlineKeyboardButton("Continue",callback_data="go"),types.InlineKeyboardButton("Break",callback_data="bal"))
   bot.send_message(c.message.chat.id,f"⚠️ WARNING {u.get('streak')} loss streak Can continue Warning only",reply_markup=k)
  k=types.InlineKeyboardMarkup(row_width=2)
  k.add(types.InlineKeyboardButton("Real 12",callback_data="real_man"),types.InlineKeyboardButton("OTC 20",callback_data="otc_man"))
  k.add(types.InlineKeyboardButton("Auto Best 3",callback_data="real_auto"))
  bot.send_message(c.message.chat.id,f"Get Signal {lvl} {used}/{lim} Choose",reply_markup=k)
 elif d=="bal":
  u=ensure(tid)
  _,used,lim=check(tid,u.get("level","free"))
  if tid==OWNER:
   lim="♾️"
  bot.send_message(c.message.chat.id,f"Status {used}/{lim} Total ${u.get('total',0)}")
 elif d=="win":
  bot.send_message(c.message.chat.id,"Win Rate 32\nEUR/USD OTC 88% GBP/USD OTC 86% BTC 84%\nSTARTER 75-82 PRO 82-89 VIP 89-95")
 elif d=="dep":
  bot.send_message(c.message.chat.id,f"Deposit Click {LINK}?click_id={tid} $20=20 $50=100 $100=♾️ Auto verified")
 elif d=="how":
  bot.send_message(c.message.chat.id,f"How to Use Register {LINK}?click_id={tid} Deposit $20 START TRADING Manual Auto Real OTC")
 elif d=="ref":
  bot.send_message(c.message.chat.id,f"Ref https://t.me/WWPocketSignalsbot?start=ref_{tid} Invited {db.get(tid,{}).get('refs',0)}")
 elif d=="sup":
  bot.send_message(c.message.chat.id,f"Support ID {tid}")
 elif d=="av" or d=="rv" or d=="ban":
  bot.send_message(c.message.chat.id,"Use /addvip ID /remvip ID /ban ID")
 elif d.startswith("real_") or d.startswith("otc_"):
  parts=d.split("_")
  mtype=parts[0]
  mode=parts[1]
  is_otc=mtype=="otc"
  tier_pairs=REAL
  if is_otc:
   tier_pairs=OTC
  if mode=="auto":
   # AUTO BEST 3
   msg="AUTO BEST 3\n\n"
   for p in tier_pairs[:3]:
    ex="1m"
    if lvl=="pro":
     ex=random.choice(["1m","2m","3m"])
    if lvl=="vip":
     ex=random.choice(["1m","2m","3m","5m"])
    txt,conf=gen(p,ex,lvl if lvl else "starter")
    msg+=txt+"\n---\n"
   inc(tid)
   bot.send_message(c.message.chat.id,msg)
  else:
   k=types.InlineKeyboardMarkup(row_width=2)
   for p in tier_pairs:
    k.add(types.InlineKeyboardButton(p,callback_data=f"p_{p.replace(' ','_')}_{mtype}"))
   bot.send_message(c.message.chat.id,f"Choose Pair {mtype} {len(tier_pairs)}",reply_markup=k)
 elif d.startswith("p_"):
  full=d[2:]
  mtype=full.split("_")[-1]
  pair="_".join(full.split("_")[:-1])
  pair=pair.replace("_"," ")
  if mtype=="otc" and "OTC" not in pair:
   pair+=" OTC"
  if not lvl:
   lvl="starter"
  exps=["1m"]
  if lvl=="pro":
   exps=["1m","2m","3m"]
  if lvl=="vip":
   exps=["1m","2m","3m","5m"]
  k=types.InlineKeyboardMarkup(row_width=3)
  for e in exps:
   k.add(types.InlineKeyboardButton(e,callback_data=f"e_{pair.replace(' ','_')}_{e}"))
  bot.send_message(c.message.chat.id,f"Expiry {pair}",reply_markup=k)
 elif d.startswith("e_"):
  full=d[2:]
  pp,ex=full.rsplit("_",1)
  pair=pp.replace("_"," ")
  if not lvl:
   lvl="starter"
  _,used,lim=check(tid,lvl)
  if used>=lim:
   bot.send_message(c.message.chat.id,f"Limit {used}/{lim}")
   bot.answer_callback_query(c.id)
   return
  txt,conf=gen(pair,ex,lvl)
  inc(tid)
  u=ensure(tid)
  if random.random()<0.3:
   u["streak"]=u.get("streak",0)+1
  else:
   u["streak"]=0
  save(db)
  bot.send_message(c.message.chat.id,txt)
  u=ensure(tid)
  if u.get("streak",0)>=4:
   k=types.InlineKeyboardMarkup(row_width=2)
   k.add(types.InlineKeyboardButton("Continue",callback_data="go"),types.InlineKeyboardButton("Break",callback_data="bal"))
   bot.send_message(c.message.chat.id,f"⚠️ WARNING {u.get('streak')} loss streak Can continue Warning only",reply_markup=k)
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
  full=f"{URL}/{TOKEN}"
  bot.set_webhook(url=full)
  print(f"Webhook {full} Full V3")
 else:
  bot.infinity_polling()
 app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))
