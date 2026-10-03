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
        print(e)

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
    for k,v in [("today",0),("date",str(date.today())),("streak",0),("banned",False),("total",0),("level","none"),("verified",False),("refs",0)]:
        if k not in u: u[k]=v
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
def home(): return "V3.5 OK - Admin+Users", 200

@app.route("/pocket_postback")
def pp():
    sec=request.args.get("secret")
    if sec!=SECRET: return "Blocked",403
    sub=request.args.get("subid") or request.args.get("click_id") or request.args.get("sub_id")
    sm=request.args.get("sum","0")
    try: amt=float(sm); gid=str(int(float(sub)))
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
    try:
        chat_id=int(gid)
        k=types.InlineKeyboardMarkup(); k.add(types.InlineKeyboardButton("START TRADING NOW",callback_data="go"))
        send_clean(chat_id, f"✅ DEPOSIT ${amt} CONFIRMED\nLevel: {lvl.upper()} Total ${tot}", reply_markup=k)
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

# ===== USER HANDLERS =====
@bot.message_handler(commands=["start"])
def start(m):
    tid=str(m.from_user.id); clean_chat(m.chat.id, m.message_id)
    if tid not in db:
        db[tid]={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False}
        save(db)
    u=ensure(tid); lvl=get_lvl(tid)
    if lvl=="banned": send_clean(m.chat.id, "🚫 Banned"); return
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🚀 GET SIGNAL",callback_data="go"))
    k.add(types.InlineKeyboardButton("💳 Deposit",callback_data="dep"),types.InlineKeyboardButton("📊 My Status",callback_data="bal"))
    k.add(types.InlineKeyboardButton("🔗 Register",url=f"{LINK}?click_id={tid}"))
    if tid==OWNER:
        k.add(types.InlineKeyboardButton("👑 ADMIN PANEL",callback_data="admin"))
    send_clean(m.chat.id, f"👋 WELCOME V3.5\nLevel: {lvl}\nLink: {LINK}?click_id={tid}", reply_markup=k)

# ===== ADMIN PANEL =====
@bot.message_handler(commands=["admin","users","stats","panel"])
def admin_cmd(m):
    if str(m.from_user.id)!=OWNER: return
    clean_chat(m.chat.id, m.message_id)
    total_users=len(db)
    verified=sum(1 for u in db.values() if u.get("verified"))
    vip=sum(1 for u in db.values() if u.get("level")=="vip")
    banned=sum(1 for u in db.values() if u.get("banned"))
    total_dep=sum(u.get("total",0) for u in db.values())
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("👥 Users List",callback_data="admin_users"),types.InlineKeyboardButton("📊 Stats",callback_data="admin_stats"))
    k.add(types.InlineKeyboardButton("📢 Broadcast",callback_data="admin_bc"),types.InlineKeyboardButton("🚫 Ban/Unban",callback_data="admin_ban"))
    k.add(types.InlineKeyboardButton("💰 Deposits",callback_data="admin_deps"),types.InlineKeyboardButton("
