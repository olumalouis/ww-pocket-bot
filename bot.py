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
        m = bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="HTML")
        last_bot_msg[chat_id] = m.message_id
        return m
    except Exception as e:
        print("send err", e)

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
    tid=str(tid)
    u = db.get(tid)
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
    # referral bonus
    inv = u.get("inv")
    if inv and inv in db and amt>=20:
        db[inv]["refs"]=db[inv].get("refs",0)+1
    tot=u.get("total",0)+amt
    lvl="none"
    if tot>=100: lvl="vip"
    elif tot>=50: lvl="pro"
    elif tot>=20: lvl="starter"
    u["total"]=tot; u["level"]=lvl; u["verified"]=True if tot>=20 else u.get("verified",False)
    db[gid]=u; save(db)
    try:
        chat_id=int(gid); clean_chat(chat_id)
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("START TRADING NOW 🚀",callback_data="go"))
        send_clean(chat_id, f"✅ <b>DEPOSIT CONFIRMED ${amt}</b>\n\nUnlocked: <b>{lvl.upper()}</b>\nTotal: ${tot}\n\nNow you have {'20/day' if lvl=='starter' else '100/day' if lvl=='pro' else 'UNLIMITED' } signals!", reply_markup=k)
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

@bot.message_handler(commands=["start","balance","deposit","status"])
def start(m):
    tid=str(m.from_user.id); clean_chat(m.chat.id, m.message_id)
    if tid not in db:
        inv=None
        args=m.text.split()
        if len(args)>1: inv=args[1].replace("ref_","")
        if inv==tid: inv=None
        db[tid]={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False,"inv":inv}
        save(db)
    u=ensure(tid); lvl=get_lvl(tid)
    if lvl=="banned": send_clean(m.chat.id, "🚫 Banned"); return
    lim_used, used, lim_max = check_limit(tid, lvl if lvl else "free")
    lim_txt = f"{used}/{lim_max}" if lvl!="vip" and tid!=OWNER else "UNL ♾️"
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🚀 GET SIGNAL",callback_data="go"))
    k.add(types.InlineKeyboardButton("💳 Deposit",callback_data="dep"),types.InlineKeyboardButton("📊 My Status",callback_data="bal"))
    k.add(types.InlineKeyboardButton("🔗 Register Link",url=f"{LINK}?click_id={tid}"))
    k.add(types.InlineKeyboardButton("👥 Referral",callback_data="ref"))
    txt = f"
