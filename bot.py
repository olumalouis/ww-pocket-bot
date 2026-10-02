import os, json, random
from datetime import datetime, date
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

#... KEEP ALL YOUR SAME CONFIG FROM BEFORE...
BASE_AFF_LINK = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
DB_FILE = "users.json"
OWNER_ID = "8188622130"
ALL_PAIRS_REAL = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/GBP", "NZD/USD", "EUR/AUD", "GBP/JPY", "BTC/USD", "ETH/USD"]
ALL_PAIRS_OTC = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "EUR/JPY OTC", "GBP/JPY OTC", "BTC/USD OTC", "ETH/USD OTC", "EUR/GBP OTC", "USD/BRL OTC"]
TIERS = {
    "starter": {"pairs": ["EUR/USD", "USD/JPY", "GBP/USD", "EUR/USD OTC", "USD/JPY OTC", "GBP/USD OTC"], "expiry_real": ["1m"], "expiry_otc": ["15s", "30s", "1m"], "name": "STARTER"},
    "pro": {"pairs": ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC"], "expiry_real": ["1m", "2m", "3m"], "expiry_otc": ["15s", "30s", "1m", "2m", "3m"], "name": "PRO"},
    "vip": {"pairs": ALL_PAIRS_REAL + ALL_PAIRS_OTC, "expiry_real": ["1m", "2m", "3m", "5m"], "expiry_otc": ["15s", "30s", "1m", "2m", "3m", "5m"], "name": "VIP"}
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
    return f"🎯 *{level.upper()} SIGNAL*\n\n💱 Pair: {pair}\n📊 Market: {market_type}\n⏰ Expiry: {expiry}\n📈 Action: {action}\n🔥 Confidence: {conf}%\nUTC: {datetime.utcnow().strftime('%H:%M')} UTC"

@app.route('/')
def home(): return "Bot Active Webhook!"
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else: return 'ok'
@app.route('/pocket_postback')
def pocket_postback():
    subid = request.args.get('subid'); sum_val = request.args.get('sum', '0')
    try:
        amount = float(sum_val); tg_id = str(int(float(subid)))
    except: return "invalid", 400
    user = users_db.get(tg_id, {"total":0, "level":"none", "referrals":0, "invited_by":None})
    total = user.get("total",0) + amount
    level = "vip" if total>=100 else "pro" if total>=50 else "starter"
    user["total"]=total; user["level"]=level; user["verified"]=True
    users_db[tg_id]=user; save_db(users_db)
    try: bot.send_message(int(tg_id), f"✅ Deposit ${amount} confirmed! Total: ${total} Level: {level.upper()} 🎉")
    except: pass
    return "ok", 200

@bot.message_handler(commands=['start'])
def start(m):
    tid=str(m.from_user.id)
    args=m.text.split()
    invited_by=args[1].replace("ref_","") if len(args)>1 and args[1].startswith("ref_") else None
    if tid not in users_db:
        users_db[tid]={"total":0,"level":"none","verified":False,"referrals":0,"invited_by":invited_by,"last_teaser":None}
        if invited_by and invited_by in users_db and invited_by!=tid:
            users_db[invited_by]["referrals"]=users_db[invited_by].get("referrals",0)+1
        save_db(users_db)
    link=f"{BASE_AFF_LINK}?click_id={tid}"
    ref_link=f"https://t.me/WWPocketSignalsbot?start=ref_{tid}"
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🎯 Get Signal", callback_data="get_signal"))
    kb.add(types.InlineKeyboardButton("💰 My Balance", callback_data="balance"),types.InlineKeyboardButton("👥 Referral", callback_data="referral"))
    kb.add(types.InlineKeyboardButton("📝 Register on Pocket", url=link))
    msg=f"👋 *WELCOME V2*\n\n💵 $20 STARTER | $50 PRO | $100 VIP\n🎁 1 free teaser/day\n\nRegister: {link}\nID: `{tid}`\nRef: {ref_link}"
    if tid==OWNER_ID: msg=f"👑 *OWNER VIP*\n{msg}"
    bot.send_message(m.chat.id, msg, reply_markup=kb, parse_mode="Markdown")

def handle_balance(m):
    tid=str(m.from_user.id); u=users_db.get(tid,{"total":0,"level":"none"})
    level=u.get("level","none").upper() if u.get("verified") or tid==OWNER_ID else "LOCKED 🔒"
    bot.send_message(m.chat.id, f"💰 Total: ${u.get('total',0)}\n🏆 Level: {level}\n👥 Ref: {u.get('referrals',0)}\nID: {tid}")
def send_teaser(m):
    tid=str(m.from_user.id); u=users_db.get(tid,{}); today=str(date.today())
    if u.get("last_teaser")==today:
        bot.send_message(m.chat.id, f"❌ Teaser used today! Deposit $20: {BASE_AFF_LINK}?click_id={tid}"); return
    u["last_teaser"]=today; users_db[tid]=u; save_db(users_db)
    bot.send_message(m.chat.id, "📊 FREE TEASER (Blurred): Pair: EUR/USD ** Action: B** ⬆️\n🔓 Deposit $20 to unlock!")
def handle_get_signal_entry(m):
    tid=str(m.from_user.id); level=get_user_level(tid)
    if not level: return send_teaser(m)
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🖐️ Manual", callback_data="mode_manual"),types.InlineKeyboardButton("🤖 Auto", callback_data="mode_auto"))
    bot.send_message(m.chat.id, f"🎯 Get Signal - {level.upper()}\nChoose mode:", reply_markup=kb, parse_mode="Markdown")
@bot.message_handler(commands=['balance','signals','analyze'])
def cmds(m):
    if m.text.startswith("/balance"): return handle_balance(m)
    if m.text.startswith("/signals"): return handle_get_signal_entry(m)
    if m.text.startswith("/analyze"):
        parts=m.text.split()
        if len(parts)<2: bot.send_message(m.chat.id, "Use: /analyze EUR/USD"); return
        pair=" ".join(parts[1:]).upper(); level=get_user_level(m.from_user.id)
        if not level: return send_teaser(m)
        is_otc="OTC" in pair; expiry_list=TIERS[level]["expiry_otc"] if is_otc else TIERS[level]["expiry_real"]
        bot.send_message(m.chat.id, generate_signal_text(pair, random.choice(expiry_list), level), parse_mode="Markdown")
@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    tid=str(c.from_user.id); level=get_user_level(tid)
    if c.data=="get_signal": handle_get_signal_entry(c.message)
    elif c.data=="balance": handle_balance(c.message)
    elif c.data=="referral":
        ref_link=f"https://t.me/WWPocketSignalsbot?start=ref_{tid}"; u=users_db.get(tid,{})
        bot.send_message(c.message.chat.id, f"👥 Ref Link: {ref_link}\nInvited: {u.get('referrals',0)}/3")
    elif c.data.startswith("mode_"):
        mode=c.data.split("_")[1]; kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("🌍 Real", callback_data=f"market_real_{mode}"),types.InlineKeyboardButton("💱 OTC", callback_data=f"market_otc_{mode}"))
        bot.edit_message_text(f"Choose Market [{mode.upper()}]:", c.message.chat.id, c.message.message_id, reply_markup=kb)
    elif c.data.startswith("market_"):
        _,mtype,mode=c.data.split("_")
        if mode=="auto":
            tier=TIERS[level]; is_otc=mtype=="otc"; expiry_list=tier["expiry_otc"] if is_otc else tier["expiry_real"]
            pairs=[p for p in tier["pairs"] if ("OTC" in p)==is_otc] or tier["pairs"][:3]
            bot.send_message(c.message.chat.id, "🤖 AUTO SCAN...\n"+generate_signal_text(random.choice(pairs), random.choice(expiry_list), level), parse_mode="Markdown")
        else:
            tier=TIERS[level]; is_otc=mtype=="otc"; pairs=[p for p in tier["pairs"] if ("OTC" in p)==is_otc]
            kb=types.InlineKeyboardMarkup(row_width=2)
            for p in pairs: kb.add(types.InlineKeyboardButton(p, callback_data=f"pair_{p.replace(' ','_')}_{mtype}"))
            bot.edit_message_text(f"Choose Pair - {mtype.upper()}:", c.message.chat.id, c.message.message_id, reply_markup=kb)
    elif c.data.startswith("pair_"):
        full=c.data[5:]; mtype=full.split("_")[-1]; pair="_".join(full.split("_")[:-1]).replace("_"," ")
        if mtype=="otc" and "OTC" not in pair: pair+=" OTC"
        expiry_list=TIERS[level]["expiry_otc"] if mtype=="otc" else TIERS[level]["expiry_real"]
        kb=types.InlineKeyboardMarkup(row_width=3)
        for exp in expiry_list: kb.add(types.InlineKeyboardButton(exp, callback_data=f"exp_{pair.replace(' ','_')}_{exp}"))
        bot.edit_message_text(f"Pair: {pair}\nChoose Expiry:", c.message.chat.id, c.message.message_id, reply_markup=kb)
    elif c.data.startswith("exp_"):
        full=c.data[4:]; pair_part,exp=full.rsplit("_",1); pair=pair_part.replace("_"," ")
        bot.send_message(c.message.chat.id, generate_signal_text(pair, exp, level), parse_mode="Markdown")
    bot.answer_callback_query(c.id)

# WEBHOOK SETUP
if __name__ == "__main__":
    bot.remove_webhook()
    import time; time.sleep(1)
    # YOU MUST SET THIS TO YOUR RAILWAY URL!
    WEBHOOK_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("WEBHOOK_URL")
    if WEBHOOK_URL:
        if not WEBHOOK_URL.startswith("https://"): WEBHOOK_URL = "https://" + WEBHOOK_URL
        full_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        bot.set_webhook(url=full_url)
        print(f"✅ Webhook set to {full_url}")
    else:
        print("⚠️ No WEBHOOK_URL set, using polling fallback")
        bot.infinity_polling()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
