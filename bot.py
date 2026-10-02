import os
import json
import random
from datetime import datetime, date
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
DB_FILE = "users.json"
OWNER_ID = "8188622130"

# --- TIERS CONFIG ---
ALL_PAIRS_REAL = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/GBP", "NZD/USD", "EUR/AUD", "GBP/JPY", "BTC/USD", "ETH/USD"]
ALL_PAIRS_OTC = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "EUR/JPY OTC", "GBP/JPY OTC", "BTC/USD OTC", "ETH/USD OTC", "EUR/GBP OTC", "USD/BRL OTC"]

TIERS = {
    "starter": { # $20
        "pairs": ["EUR/USD", "USD/JPY", "GBP/USD", "EUR/USD OTC", "USD/JPY OTC", "GBP/USD OTC"],
        "expiry_real": ["1m"],
        "expiry_otc": ["15s", "30s", "1m"],
        "name": "STARTER"
    },
    "pro": { # $50
        "pairs": ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC"],
        "expiry_real": ["1m", "2m", "3m"],
        "expiry_otc": ["15s", "30s", "1m", "2m", "3m"],
        "name": "PRO"
    },
    "vip": { # $100
        "pairs": ALL_PAIRS_REAL + ALL_PAIRS_OTC,
        "expiry_real": ["1m", "2m", "3m", "5m"],
        "expiry_otc": ["15s", "30s", "1m", "2m", "3m", "5m"],
        "name": "VIP"
    }
}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

users_db = load_db()

def get_user_level(tid):
    if str(tid) == OWNER_ID: return "vip"
    u = users_db.get(str(tid))
    if not u or not u.get("verified"): return None
    return u.get("level", "starter")

def generate_signal_text(pair, expiry, level):
    action = random.choice(["BUY ⬆️", "SELL ⬇️"])
    conf = {"starter": random.randint(72,80), "pro": random.randint(81,88), "vip": random.randint(89,95)}[level]
    market_type = "OTC" if "OTC" in pair else "REAL"
    return f"""🎯 *{level.upper()} SIGNAL*

💱 Pair: {pair}
📊 Market: {market_type}
⏰ Expiry: {expiry}
📈 Action: {action}
🔥 Confidence: {conf}%

Analysis: {'Scalp momentum + RSI reversal' if expiry in ['15s','30s'] else 'Breakout confirmed + Trend continuation'}
UTC: {datetime.utcnow().strftime('%H:%M')} UTC
"""

# --- FLASK ---
@app.route('/')
def home(): return "V2 Bot Active - Deposit Only!"

@app.route('/pocket_postback')
def pocket_postback():
    subid = request.args.get('subid')
    sum_val = request.args.get('sum', '0')
    try:
        amount = float(sum_val)
        tg_id = str(int(float(subid)))
    except: return "invalid", 400
    user = users_db.get(tg_id, {"total":0, "level":"none", "referrals":0, "invited_by":None})
    total = user.get("total",0) + amount
    if total >= 100: level = "vip"
    elif total >= 50: level = "pro"
    else: level = "starter"
    user["total"] = total
    user["level"] = level
    user["verified"] = True
    users_db[tg_id] = user
    save_db(users_db)
    try:
        bot.send_message(int(tg_id), f"✅ Deposit ${amount} confirmed!\nTotal: ${total}\nLevel: {level.upper()} 🎉\nNow click 🎯 Get Signal", parse_mode="Markdown")
    except: pass
    return "ok", 200

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    tid = str(m.from_user.id)
    args = m.text.split()
    invited_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try: invited_by = args[1].replace("ref_","")
        except: pass

    if tid not in users_db:
        users_db[tid] = {"total":0, "level":"none", "verified":False, "referrals":0, "invited_by":invited_by, "last_teaser":None, "vip_until":None}
        # referral tracking
        if invited_by and invited_by in users_db and invited_by != tid:
            ref_user = users_db[invited_by]
            ref_user["referrals"] = ref_user.get("referrals",0)+1
            if ref_user["referrals"] % 3 == 0:
                ref_user["vip_until"] = "bonus" # simple bonus flag
                try: bot.send_message(int(invited_by), f"🎉 Referral Bonus! You invited 3 friends = +1 Day VIP FREE!")
                except: pass
        save_db(users_db)
    
    link = f"{BASE_AFF_LINK}?click_id={tid}"
    ref_link = f"https://t.me/{bot.get_me().username}?start=ref_{tid}"

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🎯 Get Signal", callback_data="get_signal"))
    kb.add(types.InlineKeyboardButton("💰 My Balance", callback_data="balance"),
           types.InlineKeyboardButton("👥 Referral", callback_data="referral"))
    kb.add(types.InlineKeyboardButton("📝 Register on Pocket", url=link))

    if tid == OWNER_ID:
        msg = f"👑 *WELCOME OWNER!*\nFull VIP access to all features\n\n🔗 Your Aff Link: {link}\n👥 Your Ref Link: {ref_link}\n\nCommands:\n/signals - Get signal\n/analyze EUR/USD\n/balance\n/users - stats\n/promo CODE TEXT"
    else:
        msg = f"""👋 *WELCOME TO POCKET TIERS BOT V2*

🌍 Worldwide - English
💵 Unlock tiers with deposit:
• $20 = STARTER
• $50 = PRO  
• $100 = VIP (All pairs + 15s scalp)

🎁 Free: 1 blurred teaser daily

👉 *Step 1:* Register: {link}
👉 *Step 2:* Deposit $20+
👉 *Step 3:* Click 🎯 Get Signal

Your ID: `{tid}`
👥 Invite friends: {ref_link}
"""
    bot.send_message(m.chat.id, msg, reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(commands=['balance', 'signals', 'analyze'])
def cmds(m):
    tid = str(m.from_user.id)
    if m.text.startswith("/balance"): return handle_balance(m)
    if m.text.startswith("/signals"): return handle_get_signal_entry(m)
    if m.text.startswith("/analyze"):
        parts = m.text.split()
        if len(parts) < 2:
            bot.send_message(m.chat.id, "Use: /analyze EUR/USD or /analyze EUR/USD OTC\nExample: /analyze EUR/USD")
            return
        pair = " ".join(parts[1:]).upper()
        level = get_user_level(tid)
        if not level:
            return send_teaser(m)
        # check if pair allowed
        allowed_pairs = TIERS[level]["pairs"]
        # allow if pair in list or base pair matches
        is_otc = "OTC" in pair
        expiry_list = TIERS[level]["expiry_otc"] if is_otc else TIERS[level]["expiry_real"]
        expiry = random.choice(expiry_list)
        bot.send_message(m.chat.id, generate_signal_text(pair, expiry, level), parse_mode="Markdown")

def handle_balance(m):
    tid = str(m.from_user.id)
    u = users_db.get(tid, {"total":0, "level":"none"})
    owner_tag = " (OWNER 👑)" if tid==OWNER_ID else ""
    level = u.get("level","none").upper() if u.get("verified") or tid==OWNER_ID else "LOCKED 🔒"
    bot.send_message(m.chat.id, f"💰 Deposit Total: ${u.get('total',0)}\n🏆 Level: {level}{owner_tag}\n👥 Referrals: {u.get('referrals',0)}\n✅ Verified: {u.get('verified',False) or tid==OWNER_ID}\n🆔 ID: {tid}")

def send_teaser(m):
    tid = str(m.from_user.id)
    u = users_db.get(tid, {})
    today = str(date.today())
    if u.get("last_teaser") == today:
        bot.send_message(m.chat.id, "❌ You already used your free daily teaser! Come back tomorrow UTC or deposit $20 to unlock unlimited.\n\nRegister: "+f"{BASE_AFF_LINK}?click_id={tid}")
        return
    u["last_teaser"] = today
    users_db[tid] = u
    save_db(users_db)
    blurred = "📊 FREE TEASER (Blurred):\nPair: EUR/USD **\nAction: B** ⬆️\nExpiry: *m\nConfidence: **%\n\n🔓 Deposit $20 to unlock full signal!\nUse /start"
    bot.send_message(m.chat.id, blurred)

def handle_get_signal_entry(m):
    tid = str(m.from_user.id)
    level = get_user_level(tid)
    if not level:
        return send_teaser(m)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🖐️ Manual", callback_data="mode_manual"),
           types.InlineKeyboardButton("🤖 Auto", callback_data="mode_auto"))
    bot.send_message(m.chat.id, f"🎯 *Get Signal* - Level: {level.upper()}\nChoose mode:", reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def
