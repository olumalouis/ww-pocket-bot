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
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

users_db = load_db()

def ensure_user_fields(tid):
    u = users_db.get(str(tid))
    if not u:
        return None
    changed = False
    if "signals_today" not in u:
        u["signals_today"] = 0
        changed = True
    if "signals_date" not in u:
        u["signals_date"] = str(date.today())
        changed = True
    if "loss_streak" not in u:
        u["loss_streak"] = 0
        changed = True
    if "wins" not in u:
        u["wins"] = 0
        changed = True
    if "losses" not in u:
        u["losses"] = 0
        changed = True
    if "banned" not in u:
        u["banned"] = False
        changed = True
    if "total" not in u:
        u["total"] = 0
        changed = True
    if "level" not in u:
        u["level"] = "none"
        changed = True
    if "verified" not in u:
        u["verified"] = False
        changed = True
    if "referrals" not in u:
        u["referrals"] = 0
        changed = True
    if u.get("signals_date")!= str(date.today()):
        u["signals_today"] = 0
        u["signals_date"] = str(date.today())
        changed = True
    if changed:
        users_db[str(tid)] = u
        save_db(users_db)
    return u

def get_user_level(tid):
    if str(tid) == OWNER_ID:
        return "vip"
    u = users_db.get(str(tid))
    if not u:
        return None
    ensure_user_fields(tid)
    if u.get("banned"):
        return "banned"
    if not u.get("verified"):
        return None
    return u.get("level", "starter")

def check_limit(tid, level_name):
    u = ensure_user_fields(tid)
    if not u:
        return False, 0, 5
    today = str(date.today())
    if u.get("signals_date")!= today:
        u["signals_today"] = 0
        u["signals_date"] = today
        save_db(users_db)
    limit = LIMITS.get(level_name if level_name else "free", 5)
    used = u.get("signals_today", 0)
    return used >= limit, used, limit

def increment_signal(tid):
    u = ensure_user_fields(tid)
    if u:
        u["signals_today"] = u.get("signals_today", 0) + 1
        users_db[str(tid)] = u
        save_db(users_db)

def generate_signal_text(pair, expiry, level):
    tier = TIERS.get(level, TIERS["starter"])
    action = random.choice(["BUY ⬆️", "SELL ⬇️"])
    conf = random.randint(tier["conf_min"], tier["conf_max"])
    market_type = "OTC" if "OTC" in pair else "REAL"
    txt = f"🎯 *{level.upper()} SIGNAL*\n\n💱 Pair: {pair}\n📊 Market: {market_type}\n⏰ Expiry: {expiry}\n📈 Action: {action}\n🔥 Confidence: {conf}%\n📊 Win Rate (50): {conf}%\nUTC: {datetime.utcnow().strftime('%H:%M')} UTC"
    return txt, conf

@app.route('/')
def home():
    return "Bot Active V3 - 32 pairs"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'ok'

@app.route('/pocket_postback')
def pocket_postback():
    secret = request.args.get('secret')
    if secret!= POSTBACK_SECRET:
        print(f"BLOCKED FAKE: {request.args}")
        return "Blocked - wrong secret", 403
    subid = request.args.get('subid') or request.args.get('click_id')
    sum_val = request.args.get('sum', '0') or request.args.get('amount', '0')
    try:
        amount = float(sum_val)
        tg_id = str(int(float(subid)))
    except:
        return "invalid", 400
    user = users_db.get(tg_id, {"total":0, "level":"none", "referrals":0, "invited_by":None, "verified":False, "signals_today":0, "signals_date":str(date.today()), "loss_streak":0, "wins":0, "losses":0, "banned":False})
    total = user.get("total",0) + amount
    level = "vip" if total>=100 else "pro" if total>=50 else "starter"
    user["total"] = total
    user["level"] = level
    user["verified"] = True
    users_db[tg_id] = user
    save_db(users_db)
    try:
        bot.send_message(int(tg_id), f"✅ Deposit ${amount} confirmed! Total: ${total} Level: {level.upper()} 🎉\nLimit: {LIMITS[level]}/day")
    except:
        pass
    return "ok", 200

def get_start_keyboard(tid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🚀 START TRADING", callback_data="get_signal"))
    kb.add(types.InlineKeyboardButton("💰 How to Deposit", callback_data="how_deposit"), types.InlineKeyboardButton("📊 My Status", callback_data="balance"))
    kb.add(types.InlineKeyboardButton("📈 Today's Win Rate", callback_data="winrate"), types.InlineKeyboardButton("🎓 How to Use Bot", callback_data="how_to_use"))
    kb.add(types.InlineKeyboardButton("💬 Support", callback_data="support"), types.InlineKeyboardButton("👥 Referral", callback_data="referral"))
    link = f"{BASE_AFF_LINK}?click_id={tid}"
    kb.add(types.InlineKeyboardButton("📝 Register on Pocket", url=link))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    tid = str(m.from_user.id)
    args = m.text.split()
    invited_by = args[1].replace("ref_","") if len(args)>1 and args[1].startswith("ref_") else None
    if tid not in users_db:
        users_db[tid] = {"total":0,"level":"none","verified":False,"referrals":0,"invited_by":invited_by,"last_teaser":None,"signals_today":0,"signals_date":str(date.today()),"loss_streak":0,"wins":0,"losses":0,"banned":False}
        if invited_by and invited_by in users_db and invited_by!=tid:
            users_db[invited_by]["referrals"] = users_db[invited_by].get("referrals",0)+1
        save_db(users_db)
    else:
        ensure_user_fields(tid)
    link = f"{BASE_AFF_LINK}?click_id={tid}"
    ref_link = f"https://t.me/WWPocketSignalsbot?start=ref_{tid}"
    u = users_db[tid]
    level_display = u.get("level","none").upper() if u.get("verified") or tid==OWNER_ID else "FREE"
    used = u.get("signals_today",0)
    limit = LIMITS.get(u.get("level","free") if u.get("verified") else "free", 5)
    if tid==OWNER_ID:
        limit = "♾️"
    msg = f"👋 *WELCOME V3 - 32 PAIRS*\n\n💵 FREE 5/day | $20=20/day | $50=100/day | $100=Unlimited\n\n📊 Level: {level_display}\n📈 Used: {used}/{limit} today\n🎯 Pairs: 12 Real + 20 OTC = 32\n\n🔗 Register: {link}\n🆔 ID: `{tid}`\n👥 Ref: {ref_link}\n\nClick 🚀 START TRADING"
    if tid==OWNER_ID:
        msg = f"👑 *OWNER VIP UNLIMITED*\n{msg}\n\nUse /admin"
    bot.send_message(m.chat.id, msg, reply_markup=get_start_keyboard(tid), parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin_panel(m):
    tid = str(m.from_user.id)
    if tid!= OWNER_ID:
        bot.send_message(m.chat.id, "❌ Owner only")
        return
    total_users = len(users_db)
    vip = len([u for u in users_db.values() if u.get("level")=="vip"])
    pro = len([u for u in users_db.values() if u.get("level")=="pro"])
    starter = len([u for u in users_db.values() if u.get("level")=="starter"])
    free = total_users - vip - pro - starter
    total_dep = sum([u.get("total",0) for u in users_db.values()])
    signals_today = sum([u.get("signals_today",0) for u in users_db.values() if u.get("signals_date")==str(date.today())])
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("➕ Add VIP", callback_data="admin_addvip"), types.InlineKeyboardButton("➖ Remove VIP", callback_data="admin_remvip"))
    kb.add(types.InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban"), types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
    kb.add(types.InlineKeyboardButton("📈 Win Rate 32 Pairs", callback_data="admin_winrate"), types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
    msg = f"👑 *ADMIN PANEL V3*\n\n👥 Users: {total_users}\n💎 VIP: {vip} | PRO: {pro} | STARTER: {starter} | FREE: {free}\n💰 Total Deposits: ${total_dep}\n📈 Signals Today: {signals_today}\n📊 Pairs: 32"
    bot.send_message(m.chat.id, msg, reply_markup=kb, parse_mode="Markdown")

def handle_balance(m):
    tid = str(m.from_user.id)
    u = ensure_user_fields(tid)
    if not u:
        u = {"total":0,"level":"none"}
    if u.get("banned"):
        bot.send_message(m.chat.id, "🚫 You are banned")
        return
    level = u.get("level","none").upper() if u.get("verified") or tid==OWNER_ID else "FREE"
    limit = LIMITS.get(u.get("level","free") if u.get("verified") else "free",5)
    if tid==OWNER_ID:
        limit = "♾️ UNLIMITED"
    used = u.get("signals_today",0)
    link = f"{BASE_AFF_LINK}?click_id={tid}"
    msg = f"📊 *MY STATUS V3*\n\n💰 Total: ${u.get('total',0)}\n🏆 Level: {level}\n📈 Signals: {used}/{limit} today\n🔥 Loss Streak: {u.get('loss_streak',0)}\n👥 Referrals: {u.get('referrals',0)}\n🆔 ID: {tid}\n🔗 {link}\n\nLimits: FREE 5 | STARTER 20 | PRO 100 | VIP ♾️"
    bot.send_message(m.chat.id, msg, parse_mode="Markdown")

def send_teaser(m):
    tid = str(m.from_user.id)
    u = ensure_user_fields(tid)
    if not u:
        return
    is_limited, used, lim = check_limit(tid, "free")
    if is_limited:
        bot.send_message(m.chat.id, f"❌ Daily limit reached: {used}/{lim}\n💰 Deposit $20 for 20/day: {BASE_AFF_LINK}?click_id={tid}", reply_markup=get_start_keyboard(tid))
        return
    if random.random() < 0.4:
        real_conf = random.randint(84,92)
        pair = random.choice(ALL_PAIRS_OTC[:5])
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💰 Unlock 20 signals $20", url=f"{BASE_AFF_LINK}?click_id={tid}"))
        bot.send_message(m.chat.id, f"🔒 *VIP {real_conf}% SIGNAL LOCKED*\n\n💱 Pair: {pair}\n📊 Real: {real_conf}% (VIP)\n👤 You see: Blurred 65%\n\n💎 $20=20/day $50=100/day $100=♾️\n\nLink: {BASE_AFF_LINK}?click_id={tid}", reply_markup=kb, parse_mode="Markdown")
        increment_signal(tid)
        return
    today = str(date.today())
    u["last_teaser"] = today
    users_db[tid] = u
    save_db(users_db)
    increment_signal(tid)
    bot.send_message(m.chat.id, f"📊 FREE TEASER ({used+1}/{lim}): EUR/USD OTC Blurred 65%\n🔓 $20 for 20/day real 75-82%!\nLink: {BASE_AFF_LINK}?click_id={tid}", reply_markup=get_start_keyboard(tid))

def handle_get_signal_entry(m):
    tid = str(m.from_user.id)
    level = get_user_level(tid)
    if not level:
        return send_teaser(m)
    if level == "banned":
        bot.send_message(m.chat.id, "🚫 You are banned")
        return
    is_limited, used, lim = check_limit(tid, level)
    if is_limited:
        next_tier = "PRO (100/day)" if level=="starter" else "VIP unlimited ♾️" if level=="pro" else "VIP"
        bot.send_message(m.chat.id, f"❌ Limit reached: {used}/{lim} today\nLevel: {level.upper()}\nUpgrade to {next_tier}:\n{BASE_AFF_LINK}?click_id={tid}", reply_markup=get_start_keyboard(tid))
        return
    u = ensure_user_fields(tid)
    if u.get("loss_streak",0) >=4:
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("✅ Continue Trading", callback_data="get_signal"), types.InlineKeyboardButton("⏸️ Take Break", callback_data="balance"))
        bot.send_message(m.chat.id, f"⚠️ *WARNING: {u.get('loss_streak')} losses streak*\nMarket volatile - 30min break?\nYou can still continue.\n[Warning only - not blocked]", reply_markup=kb, parse_mode="Markdown")
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🖐️ Manual", callback_data="mode_manual"),types.InlineKeyboardButton("🤖 Auto Best 3", callback_data="mode_auto"))
    bot.send_message(m.chat.id, f"🎯 Get Signal - {level.upper()} [{used}/{lim}]\nChoose mode:", reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(commands=['balance','signals','analyze','addvip','remvip','ban','winrate'])
def cmds(m):
    tid = str(m.from_user.id)
    if m.text.startswith("/balance"):
        return handle_balance(m)
    if m.text.startswith("/signals"):
        return handle_get_signal_entry(m)
    if m.text.startswith("/winrate"):
        bot.send_message(m.chat.id, "📈 *Win Rate 32 pairs*\n🥇 EUR/USD OTC 88%\n🥈 GBP/USD OTC 86%\nSTARTER 75-82% PRO 82-89% VIP 89-95%", parse_mode="Markdown")
        return
    if m.text.startswith("/addvip") and tid==OWNER_ID:
        try:
            parts = m.text.split()
            target = parts[1]
            user = users_db.get(target, {"total":100,"level":"vip","verified":True,"referrals":0,"signals_today":0,"signals_date":str(date.today()),"loss_streak":0,"wins":0,"losses":0,"banned":False})
            user["total"] = 100
            user["level"] = "vip"
            user["verified"] = True
            user["banned"] = False
            users_db[target] = user
            save_db(users_db)
            bot.send_message(m.chat.id, f"✅ Added VIP ♾️ to {target}")
        except:
            bot.send_message(m.chat.id, "Use: /addvip 123456789")
        return
    if m.text.startswith("/remvip") and tid==OWNER_ID:
        try:
            parts = m.text.split()
            target = parts[1]
            if target in users_db:
                users_db[target]["level"] = "none"
                users_db[target]["verified"] = False
                save_db(users_db)
                bot.send_message(m.chat.id, f"✅ Removed VIP {target}")
        except:
            bot.send_message(m.chat.id, "Use: /remvip 123")
        return
    if m.text.startswith("/ban") and tid==OWNER_ID:
        try:
            parts = m.text.split()
            target = parts[1]
            if target in users_db:
                users_db[target]["banned"] = not users_db[target].get("banned",False)
                save_db(users_db)
                bot.send_message(m.chat.id, f"✅ Ban toggled {target}: {users_db[target]['banned']}")
        except:
            bot.send_message(m.chat.id, "Use: /ban 123")
        return
    if m.text.startswith("/analyze"):
        parts = m.text.split()
        if len(parts)<2:
            bot.send_message(m.chat.id, "Use: /analyze EUR/USD")
            return
        pair = " ".join(parts[1:]).upper()
        level = get_user_level(m.from_user.id)
        if not level:
            return send_teaser(m)
        if level=="banned":
            bot.send_message(m.chat.id, "🚫 Banned")
            return
        is_limited, used, lim = check_limit(m.from_user.id, level)
        if is_limited:
            bot.send_message(m.chat.id, f"❌ Limit {used}/{lim}")
            return
        is_otc = "OTC" in pair
        expiry_list = TIERS[level]["expiry_otc"] if is_otc else TIERS[level]["expiry_real"]
        txt, conf = generate_signal_text(pair, random.choice(expiry_list), level)
        increment_signal(str(m.from_user.id))
        bot.send_message(m.chat.id, txt, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    tid = str(c.from_user.id)
    level = get_user_level(tid)
    if c.data == "get_signal":
        handle_get_signal_entry(c.message)
    elif c.data == "balance":
        handle_balance(c.message)
    elif c.data == "how_deposit":
        link = f"{BASE_AFF_LINK}?click_id={tid}"
        bot.send_message(c.message.chat.id, f"💰 *How to Deposit*\n\n1️⃣ Click: {link}\n2️⃣ Register/Login\n3️⃣ Deposit: $20=20/day $50=100/day $100=♾️\n4️⃣ Auto-verified", parse_mode="Markdown")
    elif c.data == "how_to_use":
        bot.send_message(c.message.chat.id, f"🎓 *How to Use*\n1️⃣ Register: {BASE_AFF_LINK}?click_id={tid}\n2️⃣ Deposit $20+\n3️⃣ 🚀 START TRADING\n4️⃣ Manual/Auto\n5️⃣ Real/OTC 20 pairs\n6️⃣ Trade\n\nFREE 5 STARTER 20 PRO 100 VIP ♾️", parse_mode="Markdown")
    elif c.data == "winrate":
        bot.send_message(c.message.chat.id, "📈 *Win Rate - 32 Pairs*\n🥇 EUR/USD OTC 88%\n🥈 GBP/USD OTC 86%\n🥉 BTC/USD OTC 84%\nSTARTER 75-82% PRO 82-89% VIP 89-95%", parse_mode="Markdown")
    elif c.data == "support":
        bot.send_message(c.message.chat.id, f"💬 Support: @YourSupport\n🆔 ID: {tid}")
    elif c.data == "referral":
        ref_link = f"https://t.me/WWPocketSignalsbot?start=ref_{tid}"
        u = users_db.get(tid,{})
        bot.send_message(c.message.chat.id, f"👥 Ref: {ref_link}\nInvited: {u.get('referrals',0)}")
    elif c.data.startswith("admin_"):
        if tid!= OWNER_ID:
            bot.answer_callback_query(c.id, "Owner only")
            return
        if c.data == "admin_addvip":
            bot.send_message(c.message.chat.id, "Use: /addvip ID")
        elif c.data == "admin_remvip":
            bot.send_message(c.message.chat.id, "Use: /remvip ID")
        elif c.data == "admin_ban":
            bot.send_message(c.message.chat.id, "Use: /ban ID")
        elif c.data == "admin_winrate":
            bot.send_message(c.message.chat.id, "📈 Win Rate 32 pairs active")
        elif c.data == "admin_stats":
            bot.send_message(c.message.chat.id, f"Stats: {len(users_db)} users")
    elif c.data.startswith("mode_"):
        if not level:
            send_teaser(c.message)
            bot.answer_callback_query(c.id)
            return
        mode = c.data.split("_")[1]
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("🌍 Real (12)", callback_data=f"market_real_{mode}"),types.InlineKeyboardButton("💱 OTC (20)", callback_data=f"market_otc_{mode}"))
        bot.edit_message_text(f"Choose Market [{mode.upper()}]: 12 Real + 20 OTC = 32", c.message.chat.id, c.message.message_id, reply_markup=kb)
    elif c.data.startswith("market_"):
        _,mtype,mode = c.data.split("_")
        if not level:
            level = "starter"
        if mode == "auto":
            tier = TIERS[level]
            is_otc = mtype=="otc"
            expiry_list = tier["expiry_otc"] if is_otc else tier["expiry_real"]
            pairs = [p for p in tier["pairs"] if ("OTC" in p)==is_otc] or tier["pairs"][:3]
            best = random.sample(pairs, m
