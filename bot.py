import os, json, random
from datetime import datetime, date
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
DB_FILE = "users.json"
OWNER_ID = "8188622130"
POSTBACK_SECRET = os.getenv("POSTBACK_SECRET", "WW12345")

ALL_REAL = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","NZD/USD","EUR/AUD","GBP/JPY","BTC/USD","ETH/USD"]
ALL_OTC = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","BTC/USD OTC","ETH/USD OTC","EUR/GBP OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","USD/PKR OTC","USD/ARS OTC","USD/BDT OTC","USD/TRY OTC","USD/PHP OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC"]

TIERS = {
 "starter": {"pairs": ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","BTC/USD OTC","ETH/USD OTC","USD/INR OTC","USD/EGP OTC"], "expiry_real": ["1m"], "expiry_otc": ["15s","30s","1m"], "name": "STARTER", "limit": 20, "cmin":75, "cmax":82},
 "pro": {"pairs": ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","NZD/USD","EUR/AUD","GBP/JPY","EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","BTC/USD OTC","ETH/USD OTC","EUR/GBP OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","USD/PKR OTC","USD/ARS OTC"], "expiry_real": ["1m","2m","3m"], "expiry_otc": ["15s","30s","1m","2m","3m"], "name":"PRO", "limit":100, "cmin":82, "cmax":89},
 "vip": {"pairs": ALL_REAL + ALL_OTC, "expiry_real": ["1m","2m","3m","5m"], "expiry_otc": ["15s","30s","1m","2m","3m","5m"], "name":"VIP", "limit":999999, "cmin":89, "cmax":95}
}
LIMITS = {"free":5,"starter":20,"pro":100,"vip":999999}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE,'r') as f:
                return json.load(f)
        except:
            return {}
    return {}
def save_db(d):
    with open(DB_FILE,'w') as f:
        json.dump(d,f,indent=2)
users_db = load_db()

def ensure(tid):
    u = users_db.get(str(tid))
    if not u:
        return None
    if "signals_today" not in u:
        u["signals_today"]=0
    if "signals_date" not in u:
        u["signals_date"]=str(date.today())
    if "loss_streak" not in u:
        u["loss_streak"]=0
    if "wins" not in u:
        u["wins"]=0
    if "losses" not in u:
        u["losses"]=0
    if "banned" not in u:
        u["banned"]=False
    if "total" not in u:
        u["total"]=0
    if "level" not in u:
        u["level"]="none"
    if "verified" not in u:
        u["verified"]=False
    if "referrals" not in u:
        u["referrals"]=0
    if u.get("signals_date")!=str(date.today()):
        u["signals_today"]=0
        u["signals_date"]=str(date.today())
    users_db[str(tid)]=u
    save_db(users_db)
    return u

def get_level(tid):
    if str(tid)==OWNER_ID:
        return "vip"
    u=users_db.get(str(tid))
    if not u:
        return None
    ensure(tid)
    if u.get("banned"):
        return "banned"
    if not u.get("verified"):
        return None
    return u.get("level","starter")

def check_limit(tid, lvl):
    u=ensure(tid)
    if not u:
        return False,0,5
    if u.get("signals_date")!=str(date.today()):
        u["signals_today"]=0
        u["signals_date"]=str(date.today())
        save_db(users_db)
    lim=LIMITS.get(lvl if lvl else "free",5)
    used=u.get("signals_today",0)
    return used>=lim, used, lim

def inc
