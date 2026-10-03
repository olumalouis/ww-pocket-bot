import os, json, random
from datetime import date, datetime
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
SECRET = os.getenv("POSTBACK_SECRET", "WW12345")

print("Starting bot, TOKEN found:", bool(TOKEN))

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
FILE = "users.json"
OWNER = "8188622130"

REAL = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","NZD/USD","EUR/AUD","GBP/JPY","BTC/USD","ETH/USD"]
OTC = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","BTC/USD OTC","ETH/USD OTC","EUR/GBP OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","USD/PKR OTC","USD/ARS OTC","USD/BDT OTC","USD/TRY OTC","USD/PHP OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC"]

last_bot_msg = {}

def clean_chat(chat_id, user_msg_id=None):
    try:
        if user_msg_id: bot.delete_message(chat_id, user_msg_id)
    except: pass
    try:
        if chat_id in last_bot_msg: bot.delete_message(chat_id, last_bot_msg[chat_id])
    except: pass

def send_clean(chat_id, text, reply_markup=None):
    try:
        m = bot.send_message(chat_id, text, reply_markup=reply_markup)
        last_bot_msg[chat_id] = m.message_id
        return m
    except: pass

def load():
    if os.path.exists(FILE):
        try:
            with open(FILE) as f: return json.load(f)
        except: return {}
    return {}
def save(d):
    with open(FILE,"w") as f: json.dump(d,f,indent=2)
db = load()

def ensure(tid):
    u = db.get(str(tid))
    if not u: return None
    if "today" not in u: u["today"]=0
    if "date" not in u: u["date"]=str(date.today())
    if "streak" not in u: u["streak"]=0
    if "banned" not in u: u["banned"]=False
    if "total" not in u: u["total"]=0
    if "level" not in u: u["level"]="none"
    if "verified" not in u: u["verified"]=False
    if "refs" not in u: u["refs"]=0
    if str(tid)==OWNER: u["level"]="vip"; u["verified"]=True; u["banned"]=False
    if u.get("date")!=str(date.today()): u["today"]=0; u["date"]=str(date.today())
    db[str(tid)]=u; save(db); return u

def get_lvl(tid):
    if str(tid)==OWNER: return "vip"
    u=db.get(str(tid))
    if not u: return None
    ensure(tid)
    if u.get("banned"): return "banned"
    if not u.get("verified"): return None
    return u.get("level","starter")

def check(tid,lvl):
    u=ensure(tid)
    if not u: return False,0,5
    lim=5
    if lvl=="starter": lim=20
    if lvl=="pro": lim=100
    if lvl=="vip": lim=999999
    return u.get("today",0)>=lim, u.get("today",0), lim

def inc(tid):
    u=ensure(tid)
    if u: u["today"]=u.get("today",0)+1; db[str(tid)]=u; save(db)

def gen(pair,exp,lvl):
    cmin=75; cmax=82
    if lvl=="pro": cmin=82; cmax=89
    if lvl=="vip": cmin=89; cmax=95
    act=random.choice(["BUY UP","SELL DOWN"])
    conf=random.randint(cmin,cmax)
    txt=f"TARGET {lvl.upper()} {pair} {exp} {act} {conf}% {datetime.utcnow().strftime('%H:%M')}"
    return txt,conf

@app.route("/")
def home():
    return "V3.5 OK - Bot Alive", 200

@app.route("/pocket_postback")
def pp():
    sec=request.args.get("secret")
    if sec!=SECRET: return "Blocked",403
    sub=request.args.get("subid") or request.args.get("click_id")
    sm=request.args.get("sum","0")
    try:
        amt=float(sm); gid=str(int(float(sub)))
    except: return "invalid",400
    u=db.get(gid)
    if not u: u={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False}
    tot=u.get("total",0)+amt
    lvl="none"
    if tot>=100: lvl="vip"
    elif tot>=50: lvl="pro"
    elif tot>=20: lvl="starter"
    u["total"]=tot; u["level"]=lvl; u["verified"]=True if tot>=20 else False
    db[gid]=u; save(db)
    try:
        chat_id=int(gid); clean_chat(chat_id)
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("START TRADING NOW",callback_data="go"))
        send_clean(chat_id, f"DEPOSIT CONFIRMED ${amt} Unlocked {lvl.upper()} Total ${tot}", reply_markup=k)
    except: pass
    return "ok",200

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type')=='application/json':
        js=request.get_data().decode('utf-8')
        up=telebot.types.Update.de_json(js)
        bot.process_new_updates([up])
        return "ok",200
    return "bad",403

# --- all handlers same as before but using send_clean ---
@bot.message_handler(commands=["start"])
def st(m):
    tid=str(m.from_user.id); clean_chat(m.chat.id, m.message_id)
    if tid not in db:
        inv=None
        args=m.text.split()
        if len(args)>1: inv=args[1].replace("ref_","")
        db[tid]={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False,"inv":inv}
        save(db)
    u=ensure(tid)
    lim_txt="5" if not u.get("verified") else "20" if u.get("level")=="starter" else "100" if u.get("level")=="pro" else "UNL"
    if tid==OWNER: lim_txt="UNL"
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("START TRADING",callback_data="go"))
    k.add(types.InlineKeyboardButton("Deposit",callback_data="dep"),types.InlineKeyboardButton("My Status",callback_data="bal"))
    k.add(types.InlineKeyboardButton("Register",url=f"{LINK}?click_id={tid}"))
    send_clean(m.chat.id, f"WELCOME V3.5 Level {u.get('level')} Used {u.get('today')}/{lim_txt} {LINK}?click_id={tid}", reply_markup=k)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    tid=str(c.from_user.id); d=c.data; lvl=get_lvl(tid)
    try: bot.delete_message(c.message.chat.id, c.message.message_id)
    except: pass
    if d=="go":
        if not lvl:
            send_clean(c.message.chat.id, f"FREE 5/day Deposit $20 for 20/day {LINK}?click_id={tid}"); inc(tid)
