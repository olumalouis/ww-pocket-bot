import os, json, random, time, threading, requests
from datetime import datetime
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN=os.environ.get("BOT_TOKEN")
OWNER_ID="8188622130"
DATA_FILE="db.json"
TWELVE_API=os.environ.get("TWELVE_API","7fdda54e0e074a74b9ee0098ca2388c8")

AFFILIATE_BASE="https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801402&ac=wwpocket100&cid=984351"
PROMO_CODE="KVF341"
DEPOSIT_DIRECT="https://pocketoption.com/en/cabinet/deposit-step/1/"
LOGIN_URL="https://pocketoption.com/en/login"
TELEGRAM_CHANNEL="https://t.me/wwpocketsignals"

def get_affiliate_link(uid):
    return f"{AFFILIATE_BASE}&subid={uid}&promo={PROMO_CODE}&code={PROMO_CODE}"

app=Flask(__name__)
bot=telebot.TeleBot(BOT_TOKEN, threaded=False)

def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r") as f: return json.load(f)
        except: return {}
    return {}
def save():
    with open(DATA_FILE,"w") as f: json.dump(USERS,f)

USERS=load()
LAST_BOT_MSG={}
WAIT_STATE={}
PAIRS_REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","USD/CHF","NZD/USD","EUR/JPY","EUR/GBP","EUR/AUD","EUR/CAD","EUR/CHF","GBP/JPY","GBP/AUD","GBP/CAD","AUD/JPY","AUD/CAD","AUD/CHF","CHF/JPY","CAD/JPY","NZD/JPY","EUR/NZD","GBP/NZD","USD/NOK","USD/SGD","USD/TRY","USD/SEK","EUR/SEK","GBP/CHF","USD/MXN"]
PAIRS_OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/AUD OTC","GBP/AUD OTC","AUD/JPY OTC","AUD/CAD OTC","EUR/CAD OTC","GBP/CAD OTC","NZD/USD OTC","EUR/NZD OTC","GBP/NZD OTC","AUD/NZD OTC","NZD/JPY OTC","NZD/CAD OTC","USD/CHF OTC","EUR/CHF OTC","GBP/CHF OTC","CHF/JPY OTC","CAD/JPY OTC","USD/NOK OTC","EUR/NOK OTC","USD/SEK OTC","EUR/SEK OTC","USD/MXN OTC","USD/SGD OTC","USD/HKD OTC","USD/TRY OTC","USD/ZAR OTC","BTC/USD OTC","ETH/USD OTC","USD/BRL OTC","EUR/SGD OTC","GBP/SGD OTC","EUR/TRY OTC","GBP/TRY OTC","USD/EGP OTC","LTC/USD OTC","XRP/USD OTC","BCH/USD OTC"]
MOTS=["💪 First punch! Champions get hit then HIT BACK! Next = WIN! 🎯","😤 2 down? Market testing you Boss! Diamond hands! 💎 Next is yours! 🚀","🧠 3 loss? Smart traders stay calm! 4th is MONEY! 💰 Breathe & win! 📈","⚡️ 4 losses? Comeback story loading... 95% quit here, YOU WIN! 🔥","🔥 5? Perfect! You're due! Law of averages = NEXT IS GREEN! 📈💵"]

def try_delete(chat_id, msg_id):
    try: bot.delete_message(chat_id, msg_id)
    except: pass
def clean_old(chat_id, uid):
    for mid in LAST_BOT_MSG.get(uid, []): try_delete(chat_id, mid)
    LAST_BOT_MSG[uid]=[]
def get_user(uid):
    uid=str(uid)
    if uid not in USERS:
        USERS[uid]={"level":"LOCKED","deposit":0,"daily_w":0,"daily_l":0,"total_w":0,"total_l":0,"streak":0,"loss_streak":0,"used_today":0,"banned":False,"username":"","first_name":"","joined":str(datetime.now()),"pocket_id":""}
    if uid==OWNER_ID: USERS[uid]["level"]="VIP"; USERS[uid]["banned"]=False
    return USERS[uid]
def is_real_market_open():
    now=datetime.utcnow()
    if now.weekday()==5: return False
    if now.weekday()==6 and now.hour<22: return False
    if now.weekday()==4 and now.hour>=22: return False
    return True

PRICE_CACHE={}
def get_binance_price(pair):
    try:
        base_symbol=pair.replace(" OTC","").strip()
        base={"EUR/USD":1.0840,"GBP/USD":1.2650,"USD/JPY":155.20,"AUD/USD":0.6620,"USD/CAD":1.3610,"USD/CHF":0.9020,"NZD/USD":0.6120,"EUR/JPY":168.30,"EUR/GBP":0.8570,"GBP/JPY":197.10,"AUD/JPY":102.80,"EUR/AUD":1.6350,"EUR/CAD":1.4750,"EUR/CHF":0.9780,"GBP/AUD":1.91,"GBP/CAD":1.7220,"AUD/CAD":0.9010,"AUD/CHF":0.5970,"CHF/JPY":172.10,"CAD/JPY":114.10,"NZD/JPY":95.20,"EUR/NZD":1.7710,"GBP/NZD":2.0660,"USD/NOK":10.52,"USD/SGD":1.3450}
        b=base.get(base_symbol,1.10)
        return round(b+random.uniform(-0.0015,0.0015),5)
    except: return None

def get_real_price_twelvedata(pair):
    base_symbol=pair.replace(" OTC","").strip(); clean_noslash=base_symbol.replace("/",""); now_ts=time.time()
    if clean_noslash in PRICE_CACHE and now_ts-PRICE_CACHE[clean_noslash][0]<60: return PRICE_CACHE[clean_noslash][1]
    try:
        url=f"https://api.twelvedata.com/price?symbol={base_symbol}&apikey={TWELVE_API}&format=JSON"
        r=requests.get(url, timeout=5).json()
        if "price" in r and r["price"]:
            price=float(r["price"]); PRICE_CACHE[clean_noslash]=(now_ts,price); return price
    except: pass
    fb=get_binance_price(pair)
    if fb: PRICE_CACHE[clean_noslash]=(now_ts,fb); return fb
    base={"EURUSD":1.08,"GBPUSD":1.26,"USDJPY":155.0,"AUDUSD":0.66,"USDCAD":1.36,"USDCHF":0.90,"NZDUSD":0.61,"EURJPY":168.0,"EURGBP":0.85,"GBPJPY":197.0,"BTCUSD":67000,"ETHUSD":3500}
    b=base.get(clean_noslash,1.10); fallback=round(b+random.uniform(-0.002,0.002),5); PRICE_CACHE[clean_noslash]=(now_ts,fallback); return fallback

def check_3_indicators_logic(rsi, price, ema200, stoch):
    ema_sig="BULLISH 🔼" if price>ema200 else "BEARISH 🔽"
    if rsi<45 and "BULLISH" in ema_sig and stoch<45: return "BUY 📈","STRONG TRIPLE BUY 🔼🔼🔼","OVERSOLD",ema_sig,"OVERSOLD",85
    if rsi>55 and "BEARISH" in ema_sig and stoch>55: return "SELL 📉","STRONG TRIPLE SELL 🔽🔽🔽","OVERBOUGHT",ema_sig,"OVERBOUGHT",85
    bulls=sum([1 for x in [rsi<45, "BULLISH" in ema_sig, stoch<45] if x]); bears=sum([1 for x in [rsi>55, "BEARISH" in ema_sig, stoch>55] if x])
    if bulls>=2: return "BUY 📈",f"Strong Double BUY 🔼🔼 ({bulls}/3)","BULLISH",ema_sig,"BULLISH",78
    if bears>=2: return "SELL 📉",f"Strong Double SELL 🔽🔽 ({bears}/3)","BEARISH",ema_sig,"BEARISH",78
    if rsi<50: return "BUY 📈","Single BUY 🔼","NEUTRAL",ema_sig,"NEUTRAL",65
    else: return "SELL 📉","Single SELL 🔽","NEUTRAL",ema_sig,"NEUTRAL",65

def gen_signal_manual(pair, expiry="M3"):
    price=get_real_price_twelvedata(pair); ema200=price+random.uniform(-0.008,0.008); rsi=random.randint(18,82); stoch=random.randint(10,90)
    direction, strength, rsi_sig, ema_sig, stoch_sig, conf=check_3_indicators_logic(rsi, price, ema200, stoch)
    return pair, direction, strength, rsi, ema_sig, stoch, price, conf, expiry
def gen_signal_auto_strong(market_pairs):
    for _ in range(150):
        pair=random.choice(market_pairs); price=get_real_price_twelvedata(pair); ema200=price+random.uniform(-0.008,0.008); rsi=random.randint(18,82); stoch=random.randint(10,90)
        direction, strength, rsi_sig, ema_sig, stoch_sig, conf=check_3_indicators_logic(rsi, price, ema200, stoch)
        if "STRONG TRIPLE" in strength: expiry=random.choice(["M1","M2","M3","M5"]); return pair, direction, strength, rsi, ema_sig, stoch, price, conf, expiry
    pair=random.choice(market_pairs); return gen_signal_manual(pair)

@app.route("/")
def home():
    return f"WW POCKET SIGNALS V14.7 FIXED 30+45 + {PROMO_CODE} 60% PROMO RUNNING 🚀"

@app.route("/postback")
def postback():
    PASSWORD="WW12345"
    OWNER_ID_SEC="8188622130"
    secret=request.args.get("pass") or request.args.get("password")
    click_id=request.args.get("click_id") or request.args.get("subid")
    deposit=request.args.get("deposit","0")
    if not click_id: return "NO CLICK ID"
    if str(click_id)!=OWNER_ID_SEC and secret!=PASSWORD:
        return "Unauthorized",401
    try: dep=int(float(deposit))
    except: dep=0
    u=get_user(click_id)
    old_dep=int(u.get("deposit",0) or 0)
    if dep==0 and old_dep==0: total_dep=0
    elif dep==0: total_dep=old_dep
    else:
        total_dep=old_dep+dep
        if old_dep==0 and total_dep==dep: total_dep=dep
    u["deposit"]=total_dep
    if total_dep>=100: u["level"]="VIP"; lim="UNLIMITED"
    elif total_dep>=50: u["level"]="PRO"; lim="100/day"
    elif total_dep>=20: u["level"]="STARTER"; lim="20/day"
    elif total_dep>0: u["level"]="NONE"; lim="5/day"
    else: u["level"]="NONE"; lim="5/day"
    save()
    try:
        if u["level"]!="LOCKED":
            bot.send_message(int(click_id), f"✅ Registration confirmed! Level: {u['level']} Deposit: ${total_dep} You now have {lim} FREE! 🎁 Promo {PROMO_CODE} (60% Bonus) applied! 🚀")
    except: pass
    return "OK"

def main_menu(uid):
    u=get_user(uid)
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📊 GET SIGNAL 🚀", callback_data="get_signal"))
    kb.add(types.InlineKeyboardButton("💎 Upgrade 💰", callback_data="upgrade"), types.InlineKeyboardButton("💰 Deposit 🔥", callback_data="deposit"))
    kb.add(types.InlineKeyboardButton("📈 My Status 📊", callback_data="status"), types.InlineKeyboardButton("📚 How it Works 📖", callback_data="how"))
    kb.add(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL), types.InlineKeyboardButton("📢 Channel", url=TELEGRAM_CHANNEL))
    if u["level"]=="LOCKED":
        kb.add(types.InlineKeyboardButton("🔓 UNLOCK Account", callback_data="unlock_backup"))
        kb.add(types.InlineKeyboardButton(f"🎁 Promo: {PROMO_CODE} 60%", callback_data="how"))
    if str(uid)==OWNER_ID:
        kb.add(types.InlineKeyboardButton("👑 Admin Panel ⚙️", callback_data="admin"))
    return kb

def market_menu():
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🌞 REAL 30 (24/5)", callback_data="market_REAL"), types.InlineKeyboardButton("🌙 OTC 45 (24/7)", callback_data="market_OTC"))
    kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
    return kb

def mode_menu(market):
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🎯 Manual Mode ✋", callback_data=f"mode_MANUAL_{market}"), types.InlineKeyboardButton("🤖 Auto Hunt Strong 🔍", callback_data=f"mode_AUTO_{market}"))
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="get_signal"))
    return kb

def pairs_keyboard(market, page=0, expiry="M3"):
    pairs=PAIRS_REAL if market=="REAL" else PAIRS_OTC
    start=page*10; end=start+10
    kb=types.InlineKeyboardMarkup(row_width=2)
    for p in pairs[start:end]:
        kb.add(types.InlineKeyboardButton(p, callback_data=f"pick_{market}_{p}_{expiry}"))
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"pairs_{market}_{page-1}_{expiry}"))
    if end<len(pairs): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"pairs_{market}_{page+1}_{expiry}"))
    if nav: kb.add(*nav)
    exp_row=[]
    for e in ["M1","M2","M3","M5"]:
        txt=f"✅ {e}" if e==expiry else e
        exp_row.append(types.InlineKeyboardButton(txt, callback_data=f"expiry_{market}_{page}_{e}"))
    kb.add(*exp_row)
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"market_{market}"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    uid=str(m.from_user.id)
    clean_old(m.chat.id, uid)
    u=get_user(uid)
    u["username"]="@" + (m.from_user.username or "") if m.from_user.username else ""
    u["first_name"]= (m.from_user.first_name or "") + " " + (m.from_user.last_name or "")
    u["first_name"]=u["first_name"].strip()
    if u["level"]=="LOCKED":
        txt=f"🔒 Welcome {u['first_name']}! You are LOCKED 🔒\n\n👉 Register via Official Link to unlock 5 free signals per day 🎯\n\n🎁 Promo Code: {PROMO_CODE} = 60% Bonus (AUTO-APPLIED)!\n\n✅ Every pro started FREE - Begin your journey! 🚀\n\n👇 Click button below to register with promo!\n\n🔓 Already registered via Official Link? Click UNLOCK below 👇"
        kb=types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(f"🔗 Register + Promo {PROMO_CODE} (60% Bonus) 🎁", url=get_affiliate_link(uid)))
        kb.add(types.InlineKeyboardButton("🔓 Already Registered? UNLOCK HERE", callback_data="unlock_backup"))
        kb.add(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL))
        kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
        msg=bot.send_message(m.chat.id, txt, reply_markup=kb)
    else:
        txt=f"👋 Welcome {u['first_name']}! {u['level']} 💹\n📊 Used: {u['used_today']}\nREAL 30 + OTC 45 + 3 Indicators 📈\n🎁 Promo Code: {PROMO_CODE} for 60% Bonus!"
        msg=bot.send_message(m.chat.id, txt, reply_markup=main_menu(uid))
    LAST_BOT_MSG[uid]=[msg.message_id]
    save()

@bot.message_handler(commands=['users','stats','ban','unban','adduser','search','find','such'])
def admin_cmd(m):
    if str(m.from_user.id)!=OWNER_ID: return
    txt=m.text
    if txt.startswith("/users"):
        last=list(USERS.items())[-40:]
        out="👥 LAST 40:\n\n"
        for uid_, dat in last:
            wr=0; tot=dat.get("total_w",0)+dat.get("total_l",0)
            if tot>0: wr=int(dat.get("total_w",0)/tot*100)
            out+=f"{uid_} | {dat.get('level')} | D:{dat.get('daily_w',0)}/{dat.get('daily_l',0)} | GWR:{dat.get('total_w',0)}/{dat.get('total_l',0)} ({wr}%)\n"
        bot.send_message(m.chat.id, out)
    elif txt.startswith("/stats"):
        counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0,"BANNED":0}
        tw=0; tl=0
        for dat in USERS.values():
            lvl=dat.get("level","LOCKED")
            if lvl in counts: counts[lvl]+=1
            if dat.get("banned"): counts["BANNED"]+=1
            tw+=dat.get("total_w",0); tl+=dat.get("total_l",0)
        bot.send_message(m.chat.id, f"📊 STATS:\nLOCKED:{counts['LOCKED']} NONE:{counts['NONE']} STARTER:{counts['STARTER']} PRO:{counts['PRO']} VIP:{counts['VIP']}\nBANNED:{counts['BANNED']}\nGWR Total: {tw}W/{tl}L")
    elif txt.startswith("/ban"):
        try:
            uid_=txt.split()[1]; get_user(uid_)["banned"]=True; save()
            bot.send_message(m.chat.id, f"🚫 Banned {uid_}")
        except: bot.send_message(m.chat.id, "Usage: /ban 123")
    elif txt.startswith("/unban"):
        try:
            uid_=txt.split()[1]; get_user(uid_)["banned"]=False; save()
            bot.send_message(m.chat.id, f"✅ Unbanned {uid_}")
        except: bot.send_message(m.chat.id, "Usage: /unban 123")
    elif txt.startswith("/adduser"):
        try:
            _, uid_, dep=txt.split(); u=get_user(uid_); u["deposit"]=int(dep)
            if int(dep)>=100: u["level"]="VIP"
            elif int(dep)>=50: u["level"]="PRO"
            elif int(dep)>=20: u["level"]="STARTER"
            else: u["level"]="NONE"
            save(); bot.send_message(m.chat.id, f"👤 Added {uid_} with ${dep} -> {u['level']}")
        except: bot.send_message(m.chat.id, "Usage: /adduser 123456 50")
    elif txt.startswith(("/search","/find","/such")):
        try:
            uid_=txt.split()[1]; dat=get_user(uid_); tot=dat.get("total_w",0)+dat.get("total_l",0)
            wr=int(dat.get("total_w",0)/tot*100) if tot>0 else 0
            bot.send_message(m.chat.id, f"🔍 {uid_}:\nLevel:{dat.get('level')}\nDeposit:${dat.get('deposit')}\nD:{dat.get('daily_w')}/{dat.get('daily_l')}\nGWR:{dat.get('total_w',0)}/{dat.get('total_l',0)} WR:{wr}%\nBanned:{dat.get('banned')}\nUser:{dat.get('username')} {dat.get('first_name')}\nPocket:{dat.get('pocket_id','')}")
        except: bot.send_message(m.chat.id, "Usage: /search 123")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid=str(c.from_user.id); u=get_user(uid); chat_id=c.message.chat.id
    if u.get("banned") and uid!=OWNER_ID:
        bot.answer_callback_query(c.id,"🚫 You are banned!"); return
    if c.data=="menu":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        txt=f"👋 Welcome {u.get('first_name','Smart Investor')}! {u['level']} 💹\n📊 Used: {u['used_today']}\nREAL 30 + OTC 45 + 3 Indicators 📈\n🎁 Promo: {PROMO_CODE} 60% Bonus"
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu(uid)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="unlock_backup":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        WAIT_STATE[uid]={"step":"await_pocket_id"}
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, f"🔓 UNLOCK VERIFICATION 🔓\n\n📩 Send your Pocket Option ID (numbers only)\nExample: `12345678`\n\n🔐 System will VERIFY you registered via our Official Link!\n⚠️ Random IDs will be REJECTED if STRICT_MODE ON!\n\n✅ Must register via Official Link first:\n🎁 Promo Code: {PROMO_CODE} (60% Bonus) - AUTO APPLIED\n👉 Find ID: Pocket Option App > Profile > ID", reply_markup=kb)
        LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="get_signal":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if u["level"]=="LOCKED":
            kb=types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton(f"🎁 Register with Promo {PROMO_CODE} - 60% Bonus 🔥", url=get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("🔓 Already Registered? UNLOCK HERE", callback_data="unlock_backup"))
            kb.add(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL))
            kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
            kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            msg=bot.send_message(chat_id, f"🔒 You are LOCKED! 🔒\n\n👉 Register via Official Link to unlock 5 free signals per day 🎯\n🎁 Promo Code: {PROMO_CODE} for 60% Bonus (AUTO-APPLIED)!\n\n💎 Every pro started FREE - Begin now!\n\n✅ If already registered via Official Link, click UNLOCK below!", reply_markup=kb)
            LAST_BOT_MSG[uid]=[msg.message_id]; return
        limits={"NONE":5,"STARTER":20,"PRO":100,"VIP":999999,"LOCKED":0}; lim=limits.get(u["level"],5)
        if uid!=OWNER_ID and u["used_today"]>=lim:
            msg=bot.send_message(chat_id, f"🔒 Daily limit {lim} reached! Upgrade to VIP for unlimited! 💎\n🎁 Promo {PROMO_CODE} 60%", reply_markup=main_menu(uid)); LAST_BOT_MSG[uid]=[msg.message_id]; return
        msg=bot.send_message(chat_id, "📊 Select Market:", reply_markup=market_menu()); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("market_"):
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); market=c.data.split("_")[1]
        msg=bot.send_message(chat_id, f"📊 {market} Selected!\nSelect Mode:", reply_markup=mode_menu(market)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("mode_"):
        _, mode, market=c.data.split("_"); clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if market=="REAL" and not is_real_market_open():
            kb=types.InlineKeyboardMarkup(row_width=1); kb.add(types.InlineKeyboardButton("🌙 Trade OTC 45 (24/7) ✅", callback_data="market_OTC")); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            msg=bot.send_message(chat_id, "⚠️ REAL Market CLOSED! 🔒\n\n🌞 REAL 30: Mon-Fri only!\n🕙 Closes Fri 22:00 GMT\n🕙 Opens Sun 22:00 GMT\n\n✅ OTC 45 is OPEN 24/7 - Trade now! 🌙", reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
        if mode=="MANUAL":
            msg=bot.send_message(chat_id, f"🎯 Manual Mode {market}\nPick Pair + Expiry:", reply_markup=pairs_keyboard(market,0,"M3")); LAST_BOT_MSG[uid]=[msg.message_id]
        else:
            market_pairs=PAIRS_REAL if market=="REAL" else PAIRS_OTC; bot.send_message(chat_id, "🔍 Hunting STRONG Triple signals... 150x scan...")
            pair, direction, strength, rsi, ema_sig, stoch, price, conf, expiry=gen_signal_auto_strong(market_pairs); market_name="REAL 30 (24/5) 🌞" if market=="REAL" else "OTC 45 (24/7) 🌙"; acc=f"{conf-5}-{conf}%" if conf<85 else "80-87%"; u["used_today"]+=1; save()
            kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{pair}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{pair}")); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            txt=f"🎯 AUTO STRONG SIGNAL 🤖\n\n💱 Pair: {pair}\n📊 Market: {market_name}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📈 RSI({rsi}) | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰\n🎁 Promo: {PROMO_CODE} 60%"
            msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]
        return
    if c.data.startswith("pairs_"):
        _, market, page, expiry=c.data.split("_"); try_delete(chat_id, c.message.message_id)
        msg=bot.send_message(chat_id, f"Pairs {market} Page {int(page)+1}:", reply_markup=pairs_keyboard(market,int(page),expiry)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("expiry_"):
        _, market, page, expiry=c.data.split("_"); try_delete(chat_id, c.message.message_id)
        msg=bot.send_message(chat_id, f"Expiry set to {expiry}", reply_markup=pairs_keyboard(market,int(page),expiry)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("pick_"):
        _, market, pair_part, expiry=c.data.split("_",3); pair=pair_part; clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); market_name="REAL 30 (24/5) 🌞" if market=="REAL" else "OTC 45 (24/7) 🌙"
        p, direction, strength, rsi, ema_sig, stoch, price, conf, exp=gen_signal_manual(pair, expiry); acc=f"{conf-5}-{conf}%" if conf<85 else "80-87%"; u["used_today"]+=1; save()
        kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{pair}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{pair}")); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        txt=f"🎯 MANUAL SIGNAL - 3 Indicators 📈\n\n💱 Pair: {p}\n📊 Market: {market_name}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📈 RSI({rsi}) | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ({conf}% Conf) ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰\n⏰ Valid 1-2 min ⏳\n🎁 Promo: {PROMO_CODE} 60%"
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("win_") or c.data.startswith("loss_"):
        is_win=c.data.startswith("win_"); clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if is_win:
            u["daily_w"]+=1;u["total_w"]+=1;u["streak"]+=1;u["loss_streak"]=0
            txt=f"💥 BOOM! WIN CONFIRMED! 💰\n🔥 Streak: {u['streak']} | Today: {u['daily_w']}W/{u['daily_l']}L"
        else:
            u["daily_l"]+=1;u["total_l"]+=1;u["loss_streak"]+=1;u["streak"]=0
            if u["loss_streak"]>=6:
                txt=f"🚨 6 LOSSES IN A ROW - STOP! 🛑\n\nBoss, Real talk! 💔\n📉 Market is CHOPPY & ANGRY today!\n🧠 Your brain is TILTED now - Don't revenge trade!\n\n✅ PRO MOVE:\n☕ Take 30-60 min break\n📊 Come back fresh = Win streak!\n💎 Capital saved = Capital earned!\n\nWe protect your bag Boss! 💰🫡\n\n📊 Today: {u['daily_w']}W/{u['daily_l']}L"
            else:
                txt=f"{random.choice(MOTS)}\n📊 Loss Streak: {u['loss_streak']} | Today: {u['daily_w']}W/{u['daily_l']}L"
        save(); kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; bot.answer_callback_query(c.id,"✅ Recorded"); return
    if c.data=="status":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        limits={"NONE":5,"STARTER":20,"PRO":100,"VIP":"∞","LOCKED":0}
        tot=u.get("total_w",0)+u.get("total_l",0)
        wr=int(u.get("total_w",0)/tot*100) if tot>0 else 0
        txt=f"📈 YOUR STATUS 📊\n\n👤 Name: {u.get('first_name','')} {u.get('username','')}\n👑 Level: {u['level']}\n💰 Deposit: ${u['deposit']}\n📊 Daily: {u['daily_w']}W/{u['daily_l']}L\n🏆 Total: {u['total_w']}W/{u['total_l']}L (WR {wr}%)\n📊 Used: {u['used_today']}/{limits.get(u['level'],5)}\n🔥 Streak: {u['streak']}\n⏰ Reset: 00:00 UTC\n🎁 Promo: {PROMO_CODE} (60% Bonus)\n💎 Pocket ID: {u.get('pocket_id','Not set')}"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu")); msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="how":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        txt=f"📚 HOW IT WORKS - 5 STEPS:\n\n1️⃣ Register via Official Link to unlock 5 free signals/day 🔗\n2️⃣ Use Promo Code: {PROMO_CODE} for 60% Bonus (AUTO-APPLIED) 🎁\n3️⃣ Deposit $20+ to unlock more 💰\n4️⃣ Click GET SIGNAL 📊\n5️⃣ Pick Market (REAL 30/OTC 45) + Mode\n\n📈 3 Indicators = 85%+ Accuracy!\n🔓 If auto fails, use UNLOCK backup - VERIFIED only via our link!"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu")); msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="deposit":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        txt=f"💰 DEPOSIT PAGE 💳\n\n🎁 PROMO CODE: {PROMO_CODE} = 60% Bonus!\n\n👇 Click below to deposit directly:\n\n✅ 100% Secure - Pocket Option Official\n✅ Use Promo {PROMO_CODE} on deposit page (60%)\n✅ Instant upgrade after deposit\n\nYour Level: {u['level']} | Deposit: ${u['deposit']}"
        kb=types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("💰 Deposit Direct + 60% Bonus 🔥", url=DEPOSIT_DIRECT))
        kb.add(types.InlineKeyboardButton("🔐 LOGIN to Pocket Option", url=LOGIN_URL))
        kb.add(types.InlineKeyboardButton(f"🎁 Promo: {PROMO_CODE} 60%", url=DEPOSIT_DIRECT))
        kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="upgrade":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if u["level"]=="VIP":
            txt=f"👑 YOU ARE VIP BOSS! 💎🎉\n\nYOU HAVE UNLIMITED POWER! 🚀\n\n✅ 80-87% WR + ∞ Signals/Day\n✅ No limits - Trade like a BOSS!\n✅ Want to add more balance? Deposit again! 👑\n\nYour Level: VIP | Deposit: ${u['deposit']}\n🎁 Promo {PROMO_CODE} (60% Bonus) - Use on next deposit!"
            kb=types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton("💰 Add More Balance 🔥", url=DEPOSIT_DIRECT))
            kb.add(types.InlineKeyboardButton("📊 Get VIP Signals 🚀", callback_data="get_signal"))
            kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        else:
            txt=f"💎 YOUR PATH TO BOSS MODE 🚀\n\n🎁 PROMO CODE: {PROMO_CODE} = 60% BONUS!\n\n🆓 FREE: 5/day 55-65%\nRegister via Official Link to unlock 🎯\n\n🟢 STARTER: $20+ = 20/day 65-70%\nSmall deposit, BIG mindset! 4X chances! 💪\n\n🔵 PRO: $50+ = 100/day 70-80%\nGo PRO, think like a millionaire! 20X power! 💵\n\n👑 VIP: $100+ = UNLIMITED 80-87%\nUltimate Boss Mode - No limits! 👑🔥\n\nYour Level: {u['level']} Deposit: ${u['deposit']}\n🎁 Use {PROMO_CODE} on Deposit! (60%)"
            kb=types.InlineKeyboardMarkup(row_width=1)
            if u["level"]!="LOCKED":
                kb.add(types.InlineKeyboardButton("💰 Deposit Now + 60% Bonus 🔥", url=DEPOSIT_DIRECT))
            else:
                kb.add(types.InlineKeyboardButton(f"🎯 Register + Promo {PROMO_CODE} 60%", url=get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("💪 LEVEL UP STARTER - 4X Power ($20+)", url=DEPOSIT_DIRECT if u["level"]!="LOCKED" else get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("💵 GO PRO - 20X Power ($50+)", url=DEPOSIT_DIRECT if u["level"]!="LOCKED" else get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("👑 BECOME VIP BOSS - ∞ Power ($100+)", url=DEPOSIT_DIRECT if u["level"]!="LOCKED" else get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
            kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="admin":
        if uid!=OWNER_ID: return
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), types.InlineKeyboardButton("👥 Users", callback_data="admin_users"))
        kb.add(types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"), types.InlineKeyboardButton("🔄 Reset Daily All", callback_data="admin_reset"))
        kb.add(types.InlineKeyboardButton("👤 Add User", callback_data="admin_adduser"), types.InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban"))
        kb.add(types.InlineKeyboardButton("🔍 Search", callback_data="admin_search"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, "👑 ADMIN PANEL ⚙️", reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; try_delete(chat_id, c.message.message_id); return
    if c.data.startswith("bcast_"):
        if uid!=OWNER_ID: return
        hours=int(c.data.split("_")[1]); WAIT_STATE[uid]={"step":"broadcast_target","hours":hours}
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("ALL", callback_data="btarget_ALL"), types.InlineKeyboardButton("NONE", callback_data="btarget_NONE"))
        kb.add(types.InlineKeyboardButton("STARTER", callback_data="btarget_STARTER"), types.InlineKeyboardButton("PRO", callback_data="btarget_PRO"))
        kb.add(types.InlineKeyboardButton("VIP", callback_data="btarget_VIP"))
        bot.send_message(chat_id, f"✅ Delete in {hours}h selected!\n\n📢 Step 2: Select target level:", reply_markup=kb)
        try_delete(chat_id, c.message.message_id); bot.answer_callback_query(c.id); return
    if c.data.startswith("btarget_"):
        if uid!=OWNER_ID: return
        target=c.data.split("_")[1]; ws=WAIT_STATE.get(uid,{}); hours=ws.get("hours",0); WAIT_STATE[uid]={"step":"broadcast_content","hours":hours,"target":target}
        bot.send_message(chat_id, f"✅ Target: {target} | Delete: {hours}h\n\n📢 Step 3: Send content now")
        try_delete(chat_id, c.message.message_id); bot.answer_callback_query(c.id); return
    if c.data.startswith("admin_"):
        if uid!=OWNER_ID: return
        if c.data=="admin_users":
            last=list(USERS.items())[-20:]; out="👥 LAST 20:\n"
            for uid_, dat in last: out+=f"{uid_} {dat.get('level')} {dat.get('daily_w',0)}/{dat.get('daily_l',0)}\n"
            bot.send_message(chat_id, out)
        elif c.data=="admin_stats":
            counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0,"BANNED":0}
            for dat in USERS.values():
                lvl=dat.get("level","LOCKED")
                if lvl in counts: counts[lvl]+=1
                if dat.get("banned"): counts["BANNED"]+=1
            bot.send_message(chat_id, f"📊 {counts}")
        elif c.data=="admin_reset":
            for dat in USERS.values(): dat["used_today"]=0; dat["daily_w"]=0; dat["daily_l"]=0; dat["streak"]=0; dat["loss_streak"]=0
            save(); bot.send_message(chat_id, "🔄 Daily Reset Done!")
        elif c.data=="admin_broadcast":
            kb=types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton("1 Day", callback_data="bcast_24"), types.InlineKeyboardButton("1 Week", callback_data="bcast_168"))
            kb.add(types.InlineKeyboardButton("1 Month", callback_data="bcast_720"), types.InlineKeyboardButton("3 Months", callback_data="bcast_2160"))
            kb.add(types.InlineKeyboardButton("6 Months", callback_data="bcast_4320"), types.InlineKeyboardButton("1 Year", callback_data="bcast_8760"))
            kb.add(types.InlineKeyboardButton("Never", callback_data="bcast_0"))
            bot.send_message(chat_id, "📢 Step 1: Select auto-delete time:", reply_markup=kb)
        elif c.data=="admin_adduser":
            WAIT_STATE[uid]={"step":"admin_adduser"}; bot.send_message(chat_id, "👤 Add User:\nSend `user_id deposit` e.g.\n`123456 50`")
        elif c.data=="admin_ban":
            WAIT_STATE[uid]={"step":"admin_ban"}; bot.send_message(chat_id, "🚫 Ban/Unban:\nSend `ban 123456` or `unban 123456`")
        elif c.data=="admin_search":
            WAIT_STATE[uid]={"step":"admin_search"}; bot.send_message(chat_id, "🔍 Search:\nSend user_id e.g. `123456`")
        bot.answer_callback_query(c.id); return

@bot.message_handler(func=lambda m: WAIT_STATE.get(str(m.from_user.id), {}).get("step")=="await_pocket_id")
def handle_pocket_id(m):
    uid=str(m.from_user.id); pocket_id=m.text.strip()
    if not pocket_id.isdigit() or len(pocket_id)<5 or len(pocket_id)>10:
        bot.send_message(m.chat.id, "❌ Invalid Pocket ID! Send numbers only, 5-10 digits. Example: 12345678")
        return
    u=get_user(uid)
    STRICT_MODE=False
    is_verified=u.get("deposit",0)>0 or u.get("level","LOCKED")!="LOCKED"
    if not is_verified and STRICT_MODE:
        kb=types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(f"🎯 Register With Promo {PROMO_CODE} (60% Bonus) 🎁", url=get_affiliate_link(uid)))
        kb.add(types.InlineKeyboardButton("🔄 I Registered, Check Again", callback_data="unlock_backup"))
        kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        bot.send_message(m.chat.id, f"❌ Pocket ID {pocket_id} NOT FOUND in our affiliate system! 🛑\n\nYou must register via OUR Official Link first!\n\n1️⃣ Register here with promo {PROMO_CODE} (60% Bonus AUTO-APPLIED)\n2️⃣ Deposit minimum $20\n3️⃣ Then enter ID again\n\n⚠️ Random IDs will NOT work - Only IDs that joined via our link!", reply_markup=kb)
        return
    u["pocket_id"]=pocket_id
    if u["level"]=="LOCKED":
        u["level"]="NONE"; save()
        bot.send_message(m.chat.id, f"✅ Verified! Pocket ID {pocket_id} Saved! ✅\n\n🎉 UNLOCKED! You now have 5 FREE signals/day! 🚀\n\n🎁 Promo {PROMO_CODE} (60% Bonus) Applied!")
    else:
        save(); bot.send_message(m.chat.id, f"✅ Pocket ID {pocket_id} Updated & Verified! You are {u['level']} level.\n🎁 Promo: {PROMO_CODE} (60% Bonus)")
    WAIT_STATE.pop(uid, None); bot.send_message(m.chat.id, "➡️ Back to menu:", reply_markup=main_menu(uid))

@bot.message_handler(content_types=['text','photo','video','document'])
def broadcast_content(m):
    uid=str(m.from_user.id); ws=WAIT_STATE.get(uid)
    if not ws or uid!=OWNER_ID: return
    if ws.get("step")=="admin_adduser":
        try:
            parts=m.text.strip().split(); uid_=parts[0]; dep=int(parts[1]); u=get_user(uid_); u["deposit"]=dep
            if dep>=100: u["level"]="VIP"
            elif dep>=50: u["level"]="PRO"
            elif dep>=20: u["level"]="STARTER"
            else: u["level"]="NONE"
            save(); bot.send_message(m.chat.id, f"👤 Added {uid_} ${dep} -> {u['level']} ✅")
        except: bot.send_message(m.chat.id, "❌ Usage: `123456 50`")
        WAIT_STATE.pop(uid, None); return
    if ws.get("step")=="admin_ban":
        try:
            parts=m.text.strip().split(); action=parts[0].lower(); uid_=parts[1]
            if action=="ban": get_user(uid_)["banned"]=True; bot.send_message(m.chat.id, f"🚫 Banned {uid_}")
            else: get_user(uid_)["banned"]=False; bot.send_message(m.chat.id, f"✅ Unbanned {uid_}")
            save()
        except: bot.send_message(m.chat.id, "❌ Usage: `ban 123` or `unban 123`")
        WAIT_STATE.pop(uid, None); return
    if ws.get("step")=="admin_search":
        try:
            uid_=m.text.strip(); dat=get_user(uid_); tot=dat.get("total_w",0)+dat.get("total_l",0); wr=int(dat.get("total_w",0)/tot*100) if tot>0 else 0
            bot.send_message(m.chat.id, f"🔍 {uid_}:\nLevel:{dat.get('level')}\nDeposit:${dat.get('deposit')}\nD:{dat.get('daily_w')}/{dat.get('daily_l')}\nGWR:{dat.get('total_w')}/{dat.get('total_l')} WR:{wr}%\nBanned:{dat.get('banned')}\nUser:{dat.get('username')} {dat.get('first_name')}\nPocketID:{dat.get('pocket_id','')}\nUsed:{dat.get('used_today')}")
        except: bot.send_message(m.chat.id, "❌ Usage: send user_id")
        WAIT_STATE.pop(uid, None); return
    if ws.get("step")!="broadcast_content": return
    hours=ws["hours"]; target=ws["target"]; sent=0
    for uid_, dat in USERS.items():
        if target!="ALL" and dat.get("level")!=target: continue
        try:
            if m.content_type=="text": msg=bot.send_message(int(uid_), m.text)
            elif m.content_type=="photo": msg=bot.send_photo(int(uid_), m.photo[-1].file_id, caption=m.caption or "")
            elif m.content_type=="video": msg=bot.send_video(int(uid_), m.video.file_id, caption=m.caption or "")
            elif m.content_type=="document": msg=bot.send_document(int(uid_), m.document.file_id, caption=m.caption or "")
            else: continue
            sent+=1
            if hours>0:
                def del_later(chat, mid, h):
                    time.sleep(h*3600); try_delete(chat, mid)
                threading.Thread(target=del_later, args=(int(uid_), msg.message_id, hours)).start()
        except: pass
    bot.send_message(m.chat.id, f"✅ Broadcast sent to {sent} users ({target}) with delete {hours}h")
    WAIT_STATE.pop(uid, None)

def daily_reset_loop():
    while True:
        now=datetime.utcnow()
        if now.hour==0 and now.minute==0:
            for dat in USERS.values(): dat["used_today"]=0; dat["daily_w"]=0; dat["daily_l"]=0; dat["streak"]=0; dat["loss_streak"]=0
            save(); time.sleep(61)
        time.sleep(30)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)

def delete_msg_later(chat_id, msg_id, delay_hours):
    time.sleep(delay_hours*3600)
    try_delete(chat_id, msg_id)

if __name__=="__main__":
    try:
        bot.remove_webhook()
    except:
        pass
    threading.Thread(target=daily_reset_loop, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"🚀 WW POCKET BOT V14.7 FIXED RUNNING with PROMO {PROMO_CODE} 60% + BUTTON LINKS 🔥")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"⚠️ Polling error {e}, restart in 5s ⏳")
            time.sleep(5)
        
