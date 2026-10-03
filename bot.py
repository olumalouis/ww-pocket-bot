import os, json, random
from datetime import date, datetime
from flask import Flask, request
import telebot
from telebot import types
TOKEN = os.getenv("BOT_TOKEN")
SECRET = os.getenv("POSTBACK_SECRET", "WW12345")
LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
FILE = "users.json"
OWNER = "8188622130"
print("Starting bot, TOKEN found:", bool(TOKEN))
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
REAL = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","NZD/USD","EUR/AUD","GBP/JPY","BTC/USD","ETH/USD"]
OTC = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","BTC/USD OTC","ETH/USD OTC","EUR/GBP OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","USD/PKR OTC","USD/ARS OTC","USD/BDT OTC","USD/TRY OTC","USD/PHP OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC"]
EXP = ["M1","M2","M3","M5"]
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
    tid=str(tid); u=db.get(tid)
    if not u: return None
    if "today" not in u: u["today"]=0
    if "date" not in u: u["date"]=str(date.today())
    if "streak" not in u: u["streak"]=0
    if "banned" not in u: u["banned"]=False
    if "total" not in u: u["total"]=0
    if "level" not in u: u["level"]="none"
    if "verified" not in u: u["verified"]=False
    if "refs" not in u: u["refs"]=0
    if tid==OWNER: u["level"]="vip"; u["verified"]=True; u["banned"]=False
    if u.get("date")!=str(date.today()): u["today"]=0; u["date"]=str(date.today())
    db[tid]=u; save(db); return u
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
    u=ensure(tid); lim=5
    if lvl=="free": lim=5
    if lvl=="starter": lim=20
    if lvl=="pro": lim=100
    if lvl=="vip": lim=999999
    return u.get("today",0)>=lim, u.get("today",0), lim
def inc(tid):
    u=ensure(tid)
    if u: u["today"]=u.get("today",0)+1; db[str(tid)]=u; save(db)
@app.route("/")
def home(): return "V3.5 OK - Bot Alive", 200
@app.route("/pocket_postback")
def pp():
    sec=request.args.get("secret")
    if sec!=SECRET: return "Blocked",403
    sub=request.args.get("subid") or request.args.get("click_id") or request.args.get("sub_id")
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
    u["total"]=tot; u["level"]=lvl; u["verified"]=True if tot>=20 else u.get("verified",False)
    db[gid]=u; save(db)
    return "ok",200
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type')=='application/json':
        js=request.get_data().decode('utf-8')
        up=telebot.types.Update.de_json(js)
        bot.process_new_updates([up])
        return "ok",200
    return "bad",403
@bot.message_handler(commands=["start"])
def start(m):
    tid=str(m.from_user.id); clean_chat(m.chat.id, m.message_id)
    if tid not in db:
        db[tid]={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False}
        save(db)
    u=ensure(tid); lvl=get_lvl(tid)
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("GET SIGNAL",callback_data="go"))
    k.add(types.InlineKeyboardButton("Deposit",callback_data="dep"),types.InlineKeyboardButton("My Status",callback_data="bal"))
    k.add(types.InlineKeyboardButton("Register",url=f"{LINK}?click_id={tid}"))
    send_clean(m.chat.id, f"WELCOME V3.5 Level {u.get('level')} Link {LINK}?click_id={tid}", reply_markup=k)
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    tid=str(c.from_user.id); d=c.data; lvl=get_lvl(tid)
    try: bot.delete_message(c.message.chat.id, c.message.message_id)
    except: pass
    if d=="go":
        is_over, used, maxl = check_limit(tid, lvl if lvl else "free")
        if is_over and tid!=OWNER:
            send_clean(c.message.chat.id, f"LIMIT {used}/{maxl} Deposit {LINK}?click_id={tid}"); return
        inc(tid)
        pair=random.choice(REAL+OTC); exp=random.choice(EXP)
        act=random.choice(["BUY UP","SELL DOWN"])
        cmin,cmax= (75,82) if lvl!="vip" else (89,95)
        conf=random.randint(cmin,cmax)
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("NEXT SIGNAL",callback_data="go"))
        send_clean(c.message.chat.id, f"SIGNAL {pair} {exp} {act} {conf}%", reply_markup=k)
app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
