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

last_bot_msg = {}

def clean_chat(chat_id, user_msg_id=None):
    try:
        if user_msg_id:
            bot.delete_message(chat_id, user_msg_id)
    except:
        pass
    try:
        if chat_id in last_bot_msg:
            bot.delete_message(chat_id, last_bot_msg[chat_id])
    except:
        pass

def send_clean(chat_id, text, reply_markup=None):
    try:
        msg = bot.send_message(chat_id, text, reply_markup=reply_markup)
        last_bot_msg[chat_id] = msg.message_id
        return msg
    except Exception as e:
        print(f"send_clean fail {e}")

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
    if "today" not in u: u["today"]=0
    if "date" not in u: u["date"]=str(date.today())
    if "streak" not in u: u["streak"]=0
    if "banned" not in u: u["banned"]=False
    if "total" not in u: u["total"]=0
    if "level" not in u: u["level"]="none"
    if "verified" not in u: u["verified"]=False
    if "refs" not in u: u["refs"]=0
    if str(tid)==OWNER:
        u["level"]="vip"
        u["verified"]=True
        u["banned"]=False
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
    if lvl=="starter": lim=20
    if lvl=="pro": lim=100
    if lvl=="vip": lim=999999
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
    txt=f"🎯 {lvl.upper()} SIGNAL\nPair {pair}\nMarket {mt}\nExpiry {exp}\nAction {act}\nConf {conf}%\nUTC {datetime.utcnow().strftime('%H:%M')}"
    return txt,conf

@app.route("/")
def home():
    return "V3.4.1 Clean+Confirm Fixed"

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
    lvl="none"
    if tot>=100:
        lvl="vip"
    elif tot>=50:
        lvl="pro"
    elif tot>=20:
        lvl="starter"
    u["total"]=tot
    u["level"]=lvl
    if tot>=20:
        u["verified"]=True
    else:
        u["verified"]=False
    db[gid]=u
    save(db)
    try:
        chat_id = int(gid)
        clean_chat(chat_id)
        if lvl!="none":
            if lvl=="vip":
                limit_txt="♾️ Unlimited"
            elif lvl=="pro":
                limit_txt="100/day"
            else:
                limit_txt="20/day"
            k=types.InlineKeyboardMarkup()
            k.add(types.InlineKeyboardButton("🚀 START TRADING NOW",callback_data="go"))
            send_clean(chat_id, f"🎉 DEPOSIT CONFIRMED! ${amt}\n\n✅ Level Unlocked: {lvl.upper()} {limit_txt}\n💰 Total: ${tot}\n\nClick below!", reply_markup=k)
        else:
            send_clean(chat_id, f"💰 Deposit ${amt} added! Total ${tot}\nNeed $20 to unlock")
    except Exception as e:
        print(f"notify fail {gid}: {e}")
    return "ok",200

def kb_start(tid):
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🚀 START TRADING",callback_data="go"))
    k.add(types.InlineKeyboardButton("💰 Deposit",callback_data="dep"),types.InlineKeyboardButton("📊 My Status",callback_data="bal"))
    k.add(types.InlineKeyboardButton("📈 Win Rate",callback_data="win"),types.InlineKeyboardButton("🎓 How to Use",callback_data="how"))
    k.add(types.InlineKeyboardButton("
