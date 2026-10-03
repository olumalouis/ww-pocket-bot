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

ALL_PAIRS_REAL = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/GBP", "NZD/USD", "EUR/AUD", "GBP/JPY", "BTC/USD", "ETH/USD"]
ALL_PAIRS_OTC = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "EUR/JPY OTC", "GBP/JPY OTC", "BTC/USD OTC", "ETH/USD OTC", "EUR/GBP OTC", "USD/BRL OTC", "USD/INR OTC", "USD/EGP OTC", "USD/PKR OTC", "USD/ARS OTC", "USD/BDT OTC", "USD/TRY OTC", "USD/PHP OTC", "NZD/USD OTC", "EUR/AUD OTC", "GBP/AUD OTC"]

TIERS = {
    "starter": {"pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "EUR/JPY OTC", "GBP/JPY OTC", "BTC/USD OTC", "ETH/USD OTC", "USD/INR OTC", "USD/EGP OTC"], "expiry_real": ["1m"], "expiry_otc": ["15s", "30s", "1m"], "name": "STARTER", "limit": 20, "conf_min": 75, "conf_max": 82},
    "pro": {"pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/GBP", "NZD/USD", "EUR/AUD", "GBP/JPY", "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "EUR/JPY OTC", "GBP/JPY OTC", "BTC/USD OTC", "ETH/USD OTC", "EUR/GBP OTC", "USD/BRL OTC", "USD/INR OTC", "USD/EGP OTC", "USD/PKR OTC", "USD/ARS OTC"], "expiry_real": ["1m", "2m", "3m"], "expiry_otc": ["15s", "30s", "1m", "2m", "3m"], "name": "PRO", "limit": 100, "conf_min": 82, "conf_max": 89},
    "vip": {"pairs": ALL_PAIRS_REAL + ALL_PAIRS_OTC, "expiry_real": ["1m", "2m", "3m", "5m"], "expiry_otc": ["15s", "30s", "1m", "2m", "3m", "5m"], "name": "VIP", "limit": 999999, "conf_min": 89, "conf_max": 95}
}
LIMITS = {"free": 5, "starter": 20, "pro": 100, "vip": 999999}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}
def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=2)
users_db = load_db()

def ensure_user_fields(tid):
    u = users_db.get(str(tid))
    if not u: return None
    changed=False
    if "signals_today" not in u: u["signals_today"]=0; changed=True
    if "signals_date" not in u: u["signals_date"]=str(date.today()); changed=True
    if "loss_streak" not in u: u["loss_streak"]=0; changed=True
    if "wins" not in u: u["wins"]=0; changed=True
    if "losses" not in u: u["losses"]=0; changed=True
    if "banned" not in u: u["banned"]=False; changed=True
    if "total" not in u: u["total"]=0; changed=True
    if "level" not in u: u["level"]="none"; changed=True
    if "verified" not in u: u["verified"]=False; changed=True
    if "referrals" not in u: u["referrals"]=0; changed=True
    if u.get("signals_date") != str(date.today()):
        u["signals_today"]=0; u["signals_date"]=str(date.today()); changed=True
    if changed: users_db[str(tid)]=u; save_db(users_db)
    return u

def get_user_level(tid):
    if str(tid) == OWNER_ID: return "vip"
    u = users_db.get(str(tid))
    if not u: return None
    ensure_user_fields(tid)
    if u.get("banned"): return "banned"
    if not u.get("verified"): return None
    return u.get("level", "starter")

def check_limit(tid, level_name):
    u = ensure_user_fields(tid)
    if not u: return False, 0, 5
    today = str(date.today())
    if u
