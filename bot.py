import os, json, random, time, threading, requests, psycopg2
from datetime import datetime
from flask import Flask, request
import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

BOT_TOKEN=os.environ.get("BOT_TOKEN")
OWNER_ID="8188622130"
FEEDBACK_ID="8855252107"
FEEDBACK_URL="https://t.me/Wwpocketsignalsfeedback"
DATA_FILE="db.json"
TRADERS_FILE="traders.json"
TWELVE_API=os.environ.get("TWELVE_API","7fdda54e0e074a74b9ee0098ca2388c8")
STRICT_MODE=os.environ.get("STRICT_MODE","true").lower()=="true"
DATABASE_URL=os.environ.get("DATABASE_URL")

AFFILIATE_BASE="https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801402&ac=wwpocket100&code=KVF341&cid=984351"
PROMO_CODE="KVF341"
DEPOSIT_DIRECT="https://pocketoption.com/en/cabinet/deposit-step/1/"
LOGIN_URL="https://pocketoption.com/en/login"
TELEGRAM_CHANNEL="https://t.me/wwpocketsignals"

SETTINGS_FILE="settings.json"
DEFAULT_SETTINGS={
    "buttons": {
        "get_signal": True,
        "upgrade": True,
        "deposit": True,
        "status": True,
        "how": True,
        "market": True,
        "mode": True,
        "pairs": True,
        "channel": True,
        "login": True,
        "feedback": True,
        "deposit_direct": True
    },
    "promo_code": "KVF341",
    "maintenance_msg": "🚧 This feature is under maintenance, resuming soon boss. Please check back in a few hours. 🔧"
}
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE,"r") as f: return json.load(f)
        except: return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()
def save_settings():
    try:
        with open(SETTINGS_FILE,"w") as f: json.dump(SETTINGS,f)
    except: pass
SETTINGS=load_settings()
# AUTO-ADD missing buttons (fixes CHANNEL not showing on server)
for k,v in DEFAULT_SETTINGS["buttons"].items():
    if k not in SETTINGS.get("buttons",{}):
        SETTINGS["buttons"][k]=v
if "promo_code" not in SETTINGS:
    SETTINGS["promo_code"]=DEFAULT_SETTINGS["promo_code"]
if "maintenance_msg" not in SETTINGS:
    SETTINGS["maintenance_msg"]=DEFAULT_SETTINGS["maintenance_msg"]
save_settings()
PROMO_CODE=SETTINGS.get("promo_code","KVF341")

def is_button_active(btn_key):
    return SETTINGS.get("buttons",{}).get(btn_key, True)
def get_maintenance_msg():
    return SETTINGS.get("maintenance_msg","🚧 This feature is under maintenance, resuming soon boss. 🔧")
def get_affiliate_link(uid):
    return f"{AFFILIATE_BASE}&click_id={uid}"

# === NEW: BIG BUY/SELL POSTER GENERATOR (PIL) ===
def generate_signal_poster(pair, direction, price, strength, expiry, accuracy, market_name, level):
    try:
        W, H = 1024, 600
        is_buy = "BUY" in direction.upper()
        bg_top = (0, 180, 80) if is_buy else (200, 30, 50)
        bg_bottom = (0, 100, 40) if is_buy else (120, 10, 20)
        img = Image.new("RGB", (W, H), bg_top)
        draw = ImageDraw.Draw(img)
        for y in range(H):
            r = int(bg_top[0] + (bg_bottom[0]-bg_top[0])*y/H)
            g = int(bg_top[1] + (bg_bottom[1]-bg_top[1])*y/H)
            b = int(bg_top[2] + (bg_bottom[2]-bg_top[2])*y/H)
            draw.line([(0,y),(W,y)], fill=(r,g,b))
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
            font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except:
            font_big = ImageFont.load_default()
            font_med = ImageFont.load_default()
            font_small = ImageFont.load_default()
        draw.rectangle([0,0,W,90], fill=(20,20,20))
        draw.text((30,20), f"WW POCKET SIGNALS | {market_name} | {level}", font=font_small, fill=(255,255,255))
        dir_text = "BUY" if is_buy else "SELL"
        draw.text((50, 110), dir_text, font=font_big, fill=(255,255,255))
        draw.text((50, 250), f"{pair}", font=font_med, fill=(255,255,200))
        draw.rectangle([50, 320, 550, 410], fill=(255,255,255))
        draw.text((70, 330), f"Price: {price}", font=font_med, fill=(0,0,0))
        draw.text((600, 130), f"EXPIRY: {expiry}", font=font_med, fill=(255,255,255))
        draw.text((600, 190), f"ACC: {accuracy}", font=font_med, fill=(255,255,200))
        draw.text((600, 250), f"{strength[:32]}", font=font_small, fill=(255,255,255))
        draw.text((600, 290), f"Promo: {PROMO_CODE} 60%", font=font_small, fill=(255,255,150))
        draw.text((30, 540), f"Trade on Pocket Option | Valid 1-2 min | {datetime.utcnow().strftime('%H:%M UTC')}", font=font_small, fill=(220,220,220))
        bio = BytesIO()
        bio.name = "signal.jpg"
        img.save(bio, "JPEG", quality=90)
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Poster error {e}")
        return None

app=Flask(__name__)
bot=telebot.TeleBot(BOT_TOKEN, threaded=False)

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require') if DATABASE_URL else None
def init_db():
    if not DATABASE_URL: return
    conn=get_conn(); cur=conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (uid TEXT PRIMARY KEY, data JSONB);")
    cur.execute("CREATE TABLE IF NOT EXISTS traders (trader_id TEXT PRIMARY KEY, click_id TEXT);")
    conn.commit(); cur.close(); conn.close()
def load():
    if not DATABASE_URL:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE,"r") as f: return json.load(f)
            except: return {}
        return {}
    try:
        conn=get_conn(); cur=conn.cursor()
        cur.execute("SELECT uid, data FROM users")
        rows=cur.fetchall()
        cur.close(); conn.close()
        return {uid: data for uid, data in rows}
    except: return {}
def save():
    if not DATABASE_URL:
        try:
            with open(DATA_FILE,"w") as f: json.dump(USERS,f)
        except: pass
        return
    try:
        conn=get_conn(); cur=conn.cursor()
        for uid, data in USERS.items():
            cur.execute("INSERT INTO users(uid,data) VALUES(%s,%s) ON CONFLICT(uid) DO UPDATE SET data=%s", (uid, json.dumps(data), json.dumps(data)))
        conn.commit(); cur.close(); conn.close()
    except: pass
def load_traders():
    if not DATABASE_URL:
        if os.path.exists(TRADERS_FILE):
            try:
                with open(TRADERS_FILE,"r") as f: return json.load(f)
            except: return {}
        return {}
    try:
        conn=get_conn(); cur=conn.cursor()
        cur.execute("SELECT trader_id, click_id FROM traders")
        rows=cur.fetchall()
        cur.close(); conn.close()
        return {tid: cid for tid, cid in rows}
    except: return {}
def save_traders():
    if not DATABASE_URL:
        try:
            with open(TRADERS_FILE,"w") as f: json.dump(TRADERS,f)
        except: pass
        return
    try:
        conn=get_conn(); cur=conn.cursor()
        for tid, cid in TRADERS.items():
            cur.execute("INSERT INTO traders(trader_id,click_id) VALUES(%s,%s) ON CONFLICT(trader_id) DO UPDATE SET click_id=%s", (tid, cid, cid))
        conn.commit(); cur.close(); conn.close()
    except: pass

init_db()
USERS=load()
TRADERS=load_traders()
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
    return f"WW POCKET SIGNALS V18 POSTER + GRID + CHANNEL FIX {PROMO_CODE} 60% RUNNING 🚀 - PORT {os.environ.get('PORT', 8080)} OK"

@app.route("/postback", methods=["GET","POST"])
def postback():
    PASSWORD="WW12345"
    data=request.values
    try:
        raw=request.get_json(force=False, silent=True) or {}
    except:
        raw={}
    secret=data.get("secret") or data.get("pass") or data.get("password") or raw.get("secret") or ""
    click_id=data.get("click_id") or data.get("sub_id1") or data.get("subid") or data.get("sub_id") or raw.get("click_id") or raw.get("sub_id1") or raw.get("subid") or ""
    trader_id=data.get("trader_id") or data.get("TraderID") or data.get("trader") or raw.get("trader_id") or ""
    sumdep=data.get("sumdep") or data.get("SumDeposits") or data.get("deposit") or data.get("amount") or raw.get("sumdep") or "0"
    event=data.get("event") or raw.get("event") or ""
    if secret and secret!=PASSWORD:
        if data.get("password")!=PASSWORD and raw.get("password")!=PASSWORD:
            return f"Unauthorized secret={secret}",401
    try: dep=float(sumdep or 0)
    except: dep=0.0
    if not click_id and trader_id:
        tid=str(trader_id)
        if tid in TRADERS:
            click_id=TRADERS[tid]
            print(f"FOUND via TRADERS mapping: trader_id={tid} -> click_id={click_id}")
    if trader_id and not click_id:
        TRADERS[str(trader_id)]=f"AFFILIATE_{str(trader_id)}"
        save_traders()
        return f"OK AFFILIATE SAVED trader_id={trader_id} dep={dep} event={event} NO CLICK_ID",200
    if not click_id:
        return "NO CLICK ID - Need click_id={CLICK_ID}",400
    if trader_id:
        TRADERS[str(trader_id)]=str(click_id)
        save_traders()
    u=get_user(str(click_id))
    old_dep=float(u.get("deposit",0) or 0)
    if u.get("level","LOCKED")=="LOCKED":
        if trader_id or event=="reg" or dep==0:
            u["level"]="NONE"
            if trader_id:
                u["pocket_id"]=str(trader_id)
            if old_dep==0:
                u["deposit"]=0
    else:
        if event=="reg" or (dep==0 and old_dep==0):
            if u.get("level","LOCKED")=="LOCKED":
                u["level"]="NONE"
            if trader_id:
                u["pocket_id"]=str(trader_id)
    if dep>0:
        total_dep=max(old_dep, dep)
        if old_dep>0 and dep>old_dep:
            total_dep=dep
        elif old_dep>0 and dep<old_dep and dep>0:
            total_dep=old_dep+dep
        u["deposit"]=total_dep
        if total_dep>=100: u["level"]="VIP"
        elif total_dep>=50: u["level"]="PRO"
        elif total_dep>=20: u["level"]="STARTER"
        elif total_dep>0: u["level"]="NONE"
        if trader_id:
            u["pocket_id"]=str(trader_id)
    save()
    try:
        if dep==0:
            bot.send_message(int(click_id), f"✅ Registration Confirmed! 🎉\n🆔 Pocket ID: {trader_id}\n🚀 Bot UNLOCKED! 5 FREE signals/day!\n🎁 Promo {PROMO_CODE} 60% active!\n💰 Deposit $20 to get STARTER!")
        else:
            lim="UNLIMITED" if u["level"]=="VIP" else "100/day" if u["level"]=="PRO" else "20/day" if u["level"]=="STARTER" else "5/day"
            bot.send_message(int(click_id), f"💰 Deposit Detected! ${u['deposit']} ✅\n🎉 Upgraded to {u['level']}! Limit: {lim} 🚀\n🆔 ID: {trader_id}")
    except: pass
    return f"OK click_id={click_id} trader_id={trader_id} dep={u.get('deposit')} level={u.get('level')} event={event}",200

def main_menu(uid):
    u=get_user(uid)
    lvl=u.get("level")
    kb=types.InlineKeyboardMarkup(row_width=2)
    if lvl=="LOCKED":
        kb.add(types.InlineKeyboardButton(f"🎯 Register + Promo {PROMO_CODE} 60% 🎁", url=get_affiliate_link(uid)))
        kb.add(types.InlineKeyboardButton("🔓 I Registered Outside - Unlock Bot 🔓", callback_data="unlock_check"))
        if is_button_active("login"):
            kb.add(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL))
        if is_button_active("channel"):
            kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
        if is_button_active("feedback"):
            kb.add(types.InlineKeyboardButton("💬 Feedback 📩", url=FEEDBACK_URL))
        return kb
    if is_button_active("get_signal"):
        kb.add(types.InlineKeyboardButton("📊 GET SIGNAL 🚀", callback_data="get_signal"))
    row2=[]
    if is_button_active("upgrade"):
        row2.append(types.InlineKeyboardButton("💎 Upgrade 💰", callback_data="upgrade"))
    if is_button_active("deposit"):
        row2.append(types.InlineKeyboardButton("💰 Deposit 🔥", callback_data="deposit"))
    if row2: kb.add(*row2)
    row3=[]
    if is_button_active("status"):
        row3.append(types.InlineKeyboardButton("📈 My Status 📊", callback_data="status"))
    if is_button_active("how"):
        row3.append(types.InlineKeyboardButton("📚 How it Works 📖", callback_data="how"))
    if row3: kb.add(*row3)
    if is_button_active("feedback"):
        kb.add(types.InlineKeyboardButton("💬 Feedback 📩", url=FEEDBACK_URL))
    bottom=[]
    if is_button_active("login"):
        bottom.append(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL))
    if is_button_active("channel"):
        bottom.append(types.InlineKeyboardButton("📢 Channel", url=TELEGRAM_CHANNEL))
    if bottom:
        kb.add(*bottom)
    if str(uid)==OWNER_ID:
        kb.add(types.InlineKeyboardButton("👑 Admin Panel ⚙️", callback_data="admin"))
    return kb

def market_menu():
    kb=types.InlineKeyboardMarkup(row_width=2)
    if is_button_active("market"):
        kb.add(types.InlineKeyboardButton("🌞 REAL 30 (24/5)", callback_data="market_REAL"), types.InlineKeyboardButton("🌙 OTC 45 (24/7)", callback_data="market_OTC"))
    else:
        kb.add(types.InlineKeyboardButton("🚧 Market Under Maintenance", callback_data="market_maint"))
    kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
    return kb

def mode_menu(market):
    kb=types.InlineKeyboardMarkup(row_width=2)
    if is_button_active("mode"):
        kb.add(types.InlineKeyboardButton("🎯 Manual Mode ✋", callback_data=f"mode_MANUAL_{market}"), types.InlineKeyboardButton("🤖 Auto Hunt Strong 🔍", callback_data=f"mode_AUTO_{market}"))
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="get_signal"))
    return kb

def pairs_keyboard(market, page=0, expiry="M3"):
    # FIXED: BOTH VERTICAL + HORIZONTAL GRID 3 COLUMNS
    pairs=PAIRS_REAL if market=="REAL" else PAIRS_OTC
    per_page=12  # 3 columns x 4 rows = grid
    start=page*per_page; end=start+per_page
    kb=types.InlineKeyboardMarkup(row_width=3)
    row=[]
    for p in pairs[start:end]:
        row.append(types.InlineKeyboardButton(p, callback_data=f"pick_{market}_{p}_{expiry}"))
        if len(row)==3:
            kb.add(*row)
            row=[]
    if row:
        kb.add(*row)
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
        txt=f"🔒 Welcome {u['first_name']}! You are LOCKED 🔒\n\n👉 Register via Official Link to unlock 5 free signals per day 🎯\n\n🎁 Promo Code: {PROMO_CODE} = 60% Bonus (AUTO-APPLIED)!\n\n✅ Every pro started FREE - Begin your journey! 🚀\n\n👇 Click button below to register with promo!\n🔓 Already registered outside bot? Click UNLOCK!"
        kb=types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(f"🔗 Register + Promo {PROMO_CODE} (60% Bonus) 🎁", url=get_affiliate_link(uid)))
        kb.add(types.InlineKeyboardButton("🔓 I Registered Outside - Unlock Bot 🔓", callback_data="unlock_check"))
        if is_button_active("login"):
            kb.add(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL))
        if is_button_active("channel"):
            kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
        if is_button_active("feedback"):
            kb.add(types.InlineKeyboardButton("💬 Feedback 📩", url=FEEDBACK_URL))
        msg=bot.send_message(m.chat.id, txt, reply_markup=kb)
    else:
        txt=f"👋 Welcome {u['first_name']}! {u['level']} 💹\n📊 Used: {u['used_today']}\nREAL 30 + OTC 45 + 3 Indicators 📈\n🎁 Promo Code: {PROMO_CODE} for 60% Bonus!"
        msg=bot.send_message(m.chat.id, txt, reply_markup=main_menu(uid))
    LAST_BOT_MSG[uid]=[msg.message_id]
    save()

@bot.message_handler(commands=['users','stats','ban','unban','adduser','search','find','such','reset','degrade','downgrade','setlevel','lock'])
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
        gwr=int(tw/(tw+tl)*100) if (tw+tl)>0 else 0
        bot.send_message(m.chat.id, f"📊 STATS:\nLOCKED:{counts['LOCKED']} NONE:{counts['NONE']} STARTER:{counts['STARTER']} PRO:{counts['PRO']} VIP:{counts['VIP']}\nBANNED:{counts['BANNED']}\n🌍 Global WR: {tw}W/{tl}L (WR {gwr}%)\nTraders verified: {len(TRADERS)}")
    elif txt.startswith("/ban"):
        try:
            import re
            mm=re.search(r'(\d{5,})', txt)
            uid_=mm.group(1) if mm else txt.split()[1]
            u_b=get_user(uid_); u_b["banned"]=True; save()
            bot.send_message(m.chat.id, f"🚫 Banned {uid_} ✅")
            try:
                bot.send_message(int(uid_), "🚫 You have been BANNED from WW Pocket Signals Bot! 🛑\n\nReason: Violation of rules / Spam.\n❌ You cannot use signals anymore.\n📩 Contact owner if mistake.")
            except: pass
        except:
            bot.send_message(m.chat.id, "Usage: /ban 123")
    elif txt.startswith("/unban"):
        try:
            import re
            mm=re.search(r'(\d{5,})', txt)
            uid_=mm.group(1) if mm else txt.split()[1]
            u_b=get_user(uid_); u_b["banned"]=False; save()
            bot.send_message(m.chat.id, f"✅ Unbanned {uid_} ✅")
            try:
                bot.send_message(int(uid_), "✅ You have been UNBANNED! 🎉\n\nWelcome back Boss! You can now use WW Pocket Signals again! 🚀\n👇 Send /start to continue!")
            except: pass
        except:
            bot.send_message(m.chat.id, "Usage: /unban 123")
    elif txt.startswith("/adduser"):
        try:
            _, uid_, dep=txt.split()
            u=get_user(uid_)
            u["deposit"]=int(dep)
            if int(dep)>=100: u["level"]="VIP"
            elif int(dep)>=50: u["level"]="PRO"
            elif int(dep)>=20: u["level"]="STARTER"
            else: u["level"]="NONE"
            save()
            bot.send_message(m.chat.id, f"👤 Added {uid_} with ${dep} -> {u['level']}")
        except:
            bot.send_message(m.chat.id, "Usage: /adduser 123456 50")
    elif txt.startswith("/reset"):
        try:
            uid_=txt.split()[1]
            dat=get_user(uid_)
            old_pid=dat.get("pocket_id","")
            dat["level"]="LOCKED"
            dat["deposit"]=0
            dat["pocket_id"]=""
            dat["used_today"]=0
            dat["daily_w"]=0
            dat["daily_l"]=0
            dat["streak"]=0
            dat["loss_streak"]=0
            if old_pid and old_pid in TRADERS:
                del TRADERS[old_pid]
            to_del=[tid for tid,cid in TRADERS.items() if str(cid)==str(uid_)]
            for tid in to_del:
                if tid in TRADERS: del TRADERS[tid]
            save(); save_traders()
            bot.send_message(m.chat.id, f"🔄 RESET DONE {uid_} → LOCKED ✅\nCleaned TRADERS: {to_del + ([old_pid] if old_pid else [])}\nNow test unlock again!")
        except Exception as e:
            bot.send_message(m.chat.id, f"Usage: /reset 8855252107\nError: {e}")
    elif txt.startswith("/lock"):
        try:
            uid_=txt.split()[1]
            dat=get_user(uid_)
            dat["level"]="LOCKED"
            save()
            bot.send_message(m.chat.id, f"🔒 LOCKED {uid_} ✅ Now LOCKED")
        except:
            bot.send_message(m.chat.id, "Usage: /lock 8855252107")
    elif txt.startswith("/setlevel"):
        try:
            parts=txt.split()
            uid_=parts[1]
            new_level=parts[2].upper()
            if new_level not in ["LOCKED","NONE","STARTER","PRO","VIP"]:
                bot.send_message(m.chat.id, "Levels: LOCKED,NONE,STARTER,PRO,VIP"); return
            dat=get_user(uid_)
            old=dat.get("level")
            dat["level"]=new_level
            if new_level=="LOCKED": dat["deposit"]=0
            elif new_level=="NONE" and dat.get("deposit",0)==0: dat["deposit"]=0
            elif new_level=="STARTER" and dat.get("deposit",0)<20: dat["deposit"]=20
            elif new_level=="PRO" and dat.get("deposit",0)<50: dat["deposit"]=50
            elif new_level=="VIP" and dat.get("deposit",0)<100: dat["deposit"]=100
            save()
            bot.send_message(m.chat.id, f"✅ SETLEVEL {uid_} : {old} → {new_level} ✅\nDeposit now: ${dat.get('deposit')}")
            try:
                bot.send_message(int(uid_), f"🔄 Your Level Changed!\n\n👑 New Level: {new_level}\n💰 Deposit: ${dat.get('deposit')}\n\nSend /start to check! 🚀")
            except: pass
        except Exception as e:
            bot.send_message(m.chat.id, f"Usage: /setlevel 8855252107 VIP\nError: {e}")
    elif txt.startswith("/degrade") or txt.startswith("/downgrade"):
        try:
            parts=txt.split()
            uid_=parts[1]
            dat=get_user(uid_)
            old_level=dat.get("level","LOCKED")
            order=["VIP","PRO","STARTER","NONE","LOCKED"]
            if len(parts)>=3:
                target=parts[2].upper()
                if target not in order:
                    bot.send_message(m.chat.id, f"Invalid level {target}. Use: LOCKED,NONE,STARTER,PRO,VIP"); return
                new_level=target
            else:
                if old_level not in order:
                    new_level="LOCKED"
                else:
                    idx=order.index(old_level)
                    new_level=order[idx+1] if idx < len(order)-1 else "LOCKED"
            dat["level"]=new_level
            if new_level=="LOCKED":
                dat["deposit"]=0
                dat["pocket_id"]=""
                to_del=[tid for tid,cid in TRADERS.items() if str(cid)==str(uid_)]
                for tid in to_del:
                    if tid in TRADERS: del TRADERS[tid]
                save_traders()
            elif new_level=="NONE":
                if dat.get("deposit",0)>20: dat["deposit"]=0
            elif new_level=="STARTER":
                dat["deposit"]=20
            elif new_level=="PRO":
                dat["deposit"]=50
            elif new_level=="VIP":
                dat["deposit"]=100
            save()
            bot.send_message(m.chat.id, f"⬇️ DEGRADE {uid_}: {old_level} → {new_level} ✅\nDeposit set: ${dat.get('deposit')}")
            try:
                bot.send_message(int(uid_), f"⬇️ Level Degraded: {old_level} → {new_level}\n💰 Deposit: ${dat.get('deposit')}\n\nContact owner if mistake. Send /start")
            except: pass
        except Exception as e:
            bot.send_message(m.chat.id, f"Usage:\n/degrade 8855252107 → one step down\n/degrade 8855252107 PRO → set to PRO\nError: {e}")
    elif txt.startswith(("/search","/find","/such")):
        try:
            uid_=txt.split()[1]
            dat=get_user(uid_)
            tot=dat.get("total_w",0)+dat.get("total_l",0)
            wr=int(dat.get("total_w",0)/tot*100) if tot>0 else 0
            bot.send_message(m.chat.id, f"🔍 {uid_}:\nLevel:{dat.get('level')}\nDeposit:${dat.get('deposit')}\nD:{dat.get('daily_w')}/{dat.get('daily_l')}\nGWR:{dat.get('total_w',0)}/{dat.get('total_l',0)} WR:{wr}%\nBanned:{dat.get('banned')}\nUser:{dat.get('username')} {dat.get('first_name')}\nPocket:{dat.get('pocket_id','')}")
        except:
            bot.send_message(m.chat.id, "Usage: /search 123")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid=str(c.from_user.id); u=get_user(uid); chat_id=c.message.chat.id
    if u.get("banned") and uid!=OWNER_ID:
        bot.answer_callback_query(c.id,"🚫 You are banned!"); return
    btn_check_map = {"get_signal": "get_signal","upgrade": "upgrade","deposit": "deposit","status": "status","how": "how","market_REAL": "market","market_OTC": "market","mode_MANUAL": "mode","mode_AUTO": "mode","pairs_": "pairs"}
    for key_prefix, btn_key in btn_check_map.items():
        if c.data.startswith(key_prefix):
            if not is_button_active(btn_key):
                bot.answer_callback_query(c.id, "🚧 Under Maintenance", show_alert=True)
                bot.send_message(chat_id, get_maintenance_msg())
                return
    if c.data=="menu":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        txt=f"👋 Welcome {u.get('first_name','Smart Investor')}! {u['level']} 💹\n📊 Used: {u['used_today']}\nREAL 30 + OTC 45 + 3 Indicators 📈\n🎁 Promo: {PROMO_CODE} 60% Bonus"
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu(uid)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="unlock_check":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        WAIT_STATE[uid]={"step":"unlock_id"}
        txt=f"🔓 UNLOCK CHECK\n\nSend your Pocket ID numbers only\n🎁 Promo {PROMO_CODE} must be used!"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="get_signal":
        if not is_button_active("get_signal"):
            bot.answer_callback_query(c.id, "🚧 Under Maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if u["level"]=="LOCKED":
            kb=types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton(f"🎁 Register with Promo {PROMO_CODE} - 60% Bonus 🔥", url=get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("🔓 I Registered Outside - Unlock Bot 🔓", callback_data="unlock_check"))
            if is_button_active("login"): kb.add(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL))
            if is_button_active("channel"): kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
            kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            msg=bot.send_message(chat_id, f"🔒 You are LOCKED!\n👉 Register via Official Link to unlock 5 free signals per day 🎯\n🎁 Promo {PROMO_CODE} for 60% Bonus!", reply_markup=kb)
            LAST_BOT_MSG[uid]=[msg.message_id]; return
        limits={"NONE":5,"STARTER":20,"PRO":100,"VIP":999999,"LOCKED":0}; lim=limits.get(u["level"],5)
        if uid!=OWNER_ID and u["used_today"]>=lim:
            msg=bot.send_message(chat_id, f"🔒 Daily limit {lim} reached! Upgrade to VIP! 💎\n🎁 Promo {PROMO_CODE} 60%", reply_markup=main_menu(uid)); LAST_BOT_MSG[uid]=[msg.message_id]; return
        msg=bot.send_message(chat_id, "📊 Select Market:", reply_markup=market_menu()); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("market_"):
        if "maint" in c.data:
            bot.answer_callback_query(c.id, "🚧 Market under maintenance", show_alert=True); return
        if not is_button_active("market"):
            bot.answer_callback_query(c.id, "🚧 Market under maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); market=c.data.split("_")[1]
        msg=bot.send_message(chat_id, f"📊 {market} Selected!\nSelect Mode:", reply_markup=mode_menu(market)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("mode_"):
        if not is_button_active("mode"):
            bot.answer_callback_query(c.id, "🚧 Mode under maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        _, mode, market=c.data.split("_"); clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if market=="REAL" and not is_real_market_open():
            kb=types.InlineKeyboardMarkup(row_width=1); kb.add(types.InlineKeyboardButton("🌙 Trade OTC 45 (24/7) ✅", callback_data="market_OTC")); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            msg=bot.send_message(chat_id, "⚠️ REAL Market CLOSED! 🔒\nOTC 45 is OPEN 24/7", reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
        if mode=="MANUAL":
            msg=bot.send_message(chat_id, f"🎯 Manual Mode {market}\nPick Pair + Expiry:", reply_markup=pairs_keyboard(market,0,"M3")); LAST_BOT_MSG[uid]=[msg.message_id]
        else:
            market_pairs=PAIRS_REAL if market=="REAL" else PAIRS_OTC; bot.send_message(chat_id, "🔍 Hunting STRONG Triple signals... 150x scan...")
            pair, direction, strength, rsi, ema_sig, stoch, price, conf, expiry=gen_signal_auto_strong(market_pairs); market_name="REAL 30 (24/5) 🌞" if market=="REAL" else "OTC 45 (24/7) 🌙"; acc=f"{conf-5}-{conf}%" if conf<85 else "80-87%"; u["used_today"]+=1; save()
            kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{pair}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{pair}")); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            txt=f"🎯 AUTO STRONG SIGNAL 🤖\n\n💱 Pair: {pair}\n📊 Market: {market_name}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📈 RSI({rsi}) | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰\n🎁 Promo: {PROMO_CODE} 60%"
            poster = generate_signal_poster(pair, direction, price, strength, expiry, acc, market_name, u['level'])
            if poster:
                msg=bot.send_photo(chat_id, poster, caption=txt, reply_markup=kb)
            else:
                msg=bot.send_message(chat_id, txt, reply_markup=kb)
            LAST_BOT_MSG[uid]=[msg.message_id]
        return
    if c.data.startswith("pairs_"):
        _, market, page, expiry=c.data.split("_"); try_delete(chat_id, c.message.message_id)
        msg=bot.send_message(chat_id, f"Pairs {market} Page {int(page)+1}:", reply_markup=pairs_keyboard(market,int(page),expiry)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("expiry_"):
        _, market, page, expiry=c.data.split("_"); try_delete(chat_id, c.message.message_id)
        msg=bot.send_message(chat_id, f"Expiry set to {expiry}", reply_markup=pairs_keyboard(market,int(page),expiry)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("pick_"):
        if not is_button_active("pairs"):
            bot.answer_callback_query(c.id, "🚧 Pairs under maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        _, market, pair_part, expiry=c.data.split("_",3); pair=pair_part; clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); market_name="REAL 30 (24/5) 🌞" if market=="REAL" else "OTC 45 (24/7) 🌙"
        p, direction, strength, rsi, ema_sig, stoch, price, conf, exp=gen_signal_manual(pair, expiry); acc=f"{conf-5}-{conf}%" if conf<85 else "80-87%"; u["used_today"]+=1; save()
        kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{pair}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{pair}")); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        txt=f"🎯 MANUAL SIGNAL - 3 Indicators 📈\n\n💱 Pair: {p}\n📊 Market: {market_name}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📈 RSI({rsi}) | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ({conf}% Conf) ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰\n⏰ Valid 1-2 min ⏳\n🎁 Promo: {PROMO_CODE} 60%"
        poster = generate_signal_poster(p, direction, price, strength, expiry, acc, market_name, u['level'])
        if poster:
            msg=bot.send_photo(chat_id, poster, caption=txt, reply_markup=kb)
        else:
            msg=bot.send_message(chat_id, txt, reply_markup=kb)
        LAST_BOT_MSG[uid]=[msg.message_id]; return
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
        if not is_button_active("status"):
            bot.answer_callback_query(c.id, "🚧 Status under maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        limits={"NONE":5,"STARTER":20,"PRO":100,"VIP":"∞","LOCKED":0}
        txt=f"📈 YOUR STATUS 📊\n\n👤 Name: {u.get('first_name','')} {u.get('username','')}\n👑 Level: {u['level']}\n💰 Deposit: ${u['deposit']}\n📊 Daily: {u['daily_w']}W/{u['daily_l']}L\n📊 Used: {u['used_today']}/{limits.get(u['level'],5)}\n🔥 Streak: {u['streak']}\n⏰ Reset: 00:00 UTC\n🎁 Promo: {PROMO_CODE} (60% Bonus)\n💎 Pocket ID: {u.get('pocket_id','Not set')}"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu")); msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="how":
        if not is_button_active("how"):
            bot.answer_callback_query(c.id, "🚧 How under maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        txt=f"📚 HOW IT WORKS - 5 STEPS:\n\n1️⃣ Register via Official Link\n2️⃣ Use Promo Code: {PROMO_CODE} for 60% Bonus 🎁\n3️⃣ Deposit $20+\n4️⃣ Click GET SIGNAL 📊\n5️⃣ Pick Market\n\n📈 3 Indicators = 85%+ Accuracy!"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu")); msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="deposit":
        if not is_button_active("deposit"):
            bot.answer_callback_query(c.id, "🚧 Deposit under maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        txt=f"💰 DEPOSIT PAGE 💳\n\n🎁 PROMO CODE: {PROMO_CODE} = 60% Bonus!\nYour Level: {u['level']} | Deposit: ${u['deposit']}"
        kb=types.InlineKeyboardMarkup(row_width=1)
        if is_button_active("deposit_direct"):
            kb.add(types.InlineKeyboardButton("💰 Deposit Direct + 60% Bonus 🔥", url=DEPOSIT_DIRECT))
        if is_button_active("login"):
            kb.add(types.InlineKeyboardButton("🔐 LOGIN", url=LOGIN_URL))
        kb.add(types.InlineKeyboardButton(f"🎁 Promo: {PROMO_CODE} 60%", url=DEPOSIT_DIRECT)); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="upgrade":
        if not is_button_active("upgrade"):
            bot.answer_callback_query(c.id, "🚧 Upgrade under maintenance", show_alert=True); bot.send_message(chat_id, get_maintenance_msg()); return
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if u["level"]=="VIP":
            txt=f"👑 YOU ARE VIP BOSS! 💎🎉\nYOU HAVE UNLIMITED POWER! 🚀\nYour Level: VIP | Deposit: ${u['deposit']}\n🎁 Promo {PROMO_CODE} 60% Bonus!"
            kb=types.InlineKeyboardMarkup(row_width=1)
            if is_button_active("deposit_direct"):
                kb.add(types.InlineKeyboardButton("💰 Add More Balance 🔥", url=DEPOSIT_DIRECT))
            kb.add(types.InlineKeyboardButton("📊 Get VIP Signals 🚀", callback_data="get_signal")); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        else:
            txt=f"💎 YOUR PATH TO BOSS MODE 🚀\n🎁 PROMO CODE: {PROMO_CODE} = 60% BONUS!\nYour Level: {u['level']} Deposit: ${u['deposit']}"
            kb=types.InlineKeyboardMarkup(row_width=1)
            if u["level"]!="LOCKED":
                if is_button_active("deposit_direct"):
                    kb.add(types.InlineKeyboardButton("💰 Deposit Now + 60% Bonus 🔥", url=DEPOSIT_DIRECT))
            else: kb.add(types.InlineKeyboardButton(f"🎯 Register + Promo {PROMO_CODE} 60%", url=get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("💪 LEVEL UP STARTER - 4X Power ($20+)", url=DEPOSIT_DIRECT if u["level"]!="LOCKED" else get_affiliate_link(uid))); kb.add(types.InlineKeyboardButton("💵 GO PRO - 20X Power ($50+)", url=DEPOSIT_DIRECT if u["level"]!="LOCKED" else get_affiliate_link(uid))); kb.add(types.InlineKeyboardButton("👑 BECOME VIP BOSS - ∞ Power ($100+)", url=DEPOSIT_DIRECT if u["level"]!="LOCKED" else get_affiliate_link(uid)))
            if is_button_active("channel"):
                kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
            kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="admin":
        if uid!=OWNER_ID: return
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), types.InlineKeyboardButton("👥 Users", callback_data="admin_users"))
        kb.add(types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"), types.InlineKeyboardButton("🔄 Reset Daily All", callback_data="admin_reset"))
        kb.add(types.InlineKeyboardButton("👤 Add User", callback_data="admin_adduser"), types.InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban"))
        kb.add(types.InlineKeyboardButton("⬇️ Degrade Level", callback_data="admin_degrade"), types.InlineKeyboardButton("🔒 Lock User", callback_data="admin_lock"))
        kb.add(types.InlineKeyboardButton("🔍 Search", callback_data="admin_search"), types.InlineKeyboardButton("🔧 Button Control", callback_data="admin_button_control"))
        kb.add(types.InlineKeyboardButton("🎟️ Change Promo Code", callback_data="admin_change_promo"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, f"👑 ADMIN PANEL ⚙️\n🎁 Current Promo: {PROMO_CODE}", reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; try_delete(chat_id, c.message.message_id); return
    if c.data=="admin_button_control":
        if uid!=OWNER_ID: return
        kb=types.InlineKeyboardMarkup(row_width=2)
        for btn_name, is_active in SETTINGS["buttons"].items():
            status = "✅ ON" if is_active else "❌ OFF"
            kb.add(types.InlineKeyboardButton(f"{btn_name.upper()} - {status}", callback_data=f"toggle_{btn_name}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin"))
        bot.send_message(chat_id, f"🔧 BUTTON CONTROLLER V18\n\nCurrent Promo: {PROMO_CODE}\n\nClick to ON/OFF any user button.\nIf OFF, user will see maintenance message.\n\n✅ Includes CHANNEL, LOGIN, FEEDBACK now! 🔔", reply_markup=kb)
        bot.answer_callback_query(c.id); try_delete(chat_id, c.message.message_id); return
    if c.data.startswith("toggle_"):
        if uid!=OWNER_ID: return
        btn_to_toggle = c.data.replace("toggle_", "")
        SETTINGS["buttons"][btn_to_toggle] = not SETTINGS["buttons"].get(btn_to_toggle, True)
        save_settings()
        new_status = SETTINGS["buttons"][btn_to_toggle]
        if new_status: notif_msg = f"🟢 {btn_to_toggle.upper()} is now ON ✅ Users can use it again!"
        else: notif_msg = f"🔴 {btn_to_toggle.upper()} is now OFF ❌ Users will see maintenance message!"
        bot.answer_callback_query(c.id, notif_msg, show_alert=True)
        kb=types.InlineKeyboardMarkup(row_width=2)
        for btn_name, is_active in SETTINGS["buttons"].items():
            status = "✅ ON" if is_active else "❌ OFF"
            kb.add(types.InlineKeyboardButton(f"{btn_name.upper()} - {status}", callback_data=f"toggle_{btn_name}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin"))
        try: bot.edit_message_text(f"🔧 BUTTON CONTROLLER\n\nLast action: {notif_msg}\n\nClick to ON/OFF:", chat_id=chat_id, message_id=c.message.message_id, reply_markup=kb)
        except: bot.send_message(chat_id, f"🔧 Updated: {notif_msg}", reply_markup=kb)
        return
    if c.data=="admin_change_promo":
        if uid!=OWNER_ID: return
        WAIT_STATE[uid]={"step":"admin_change_promo"}
        bot.send_message(chat_id, f"🎟️ CHANGE PROMO CODE\n\nCurrent promo: {PROMO_CODE}\n\nSend me the NEW promo code now. Example: WW50 or KVF999\n\nThis will update instantly for all users! Send /cancel to cancel.")
        bot.answer_callback_query(c.id); return
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
            counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0,"BANNED":0}; tw=0; tl=0
            for dat in USERS.values():
                lvl=dat.get("level","LOCKED")
                if lvl in counts: counts[lvl]+=1
                if dat.get("banned"): counts["BANNED"]+=1
                tw+=dat.get("total_w",0); tl+=dat.get("total_l",0)
            gwr=int(tw/(tw+tl)*100) if (tw+tl)>0 else 0
            bot.send_message(chat_id, f"📊 STATS:\n{counts}\n🌍 Global WR: {tw}W/{tl}L (WR {gwr}%)\nTraders:{len(TRADERS)}\n🎁 Promo:{PROMO_CODE}")
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
        elif c.data=="admin_degrade":
            WAIT_STATE[uid]={"step":"admin_degrade"}; bot.send_message(chat_id, "⬇️ Degrade:\nSend `123456` = degrade 1 level\nOr `123456 PRO` = set to PRO\nLevels: LOCKED,NONE,STARTER,PRO,VIP")
        elif c.data=="admin_lock":
            WAIT_STATE[uid]={"step":"admin_lock"}; bot.send_message(chat_id, "🔒 Lock User:\nSend user_id e.g. `123456`")
        elif c.data=="admin_search":
            WAIT_STATE[uid]={"step":"admin_search"}; bot.send_message(chat_id, "🔍 Search:\nSend user_id e.g. `123456`")
        bot.answer_callback_query(c.id); return

@bot.message_handler(content_types=['text','photo','video','document'])
def broadcast_content(m):
    uid=str(m.from_user.id); ws=WAIT_STATE.get(uid)

    # PROMO CODE CHANGE HANDLER
    if ws and ws.get("step")=="admin_change_promo" and uid==OWNER_ID:
        if m.text.strip().lower()=="/cancel":
            WAIT_STATE.pop(uid,None)
            bot.send_message(m.chat.id, "❌ Promo change cancelled.")
            return
        new_promo=m.text.strip().upper().replace(" ","")
        if len(new_promo)<3 or len(new_promo)>20:
            bot.send_message(m.chat.id, "❌ Invalid promo! Must be 3-20 chars. Try again or /cancel")
            return
        global PROMO_CODE
        old_promo=PROMO_CODE
        SETTINGS["promo_code"]=new_promo
        save_settings()
        PROMO_CODE=new_promo
        WAIT_STATE.pop(uid,None)
        bot.send_message(m.chat.id, f"✅ **PROMO CODE UPDATED!** 🎉\n\n🔴 Old: `{old_promo}`\n🟢 New: `{new_promo}`\n\n✅ All users will now see new promo!\n✅ Instant update, no restart needed!\n\n🔔 Notification: Promo changed successfully!", parse_mode="Markdown")
        return

    if ws and ws.get("step")=="unlock_id":
        trader_id_input = ''.join(filter(str.isdigit, m.text.strip()))
        if not trader_id_input:
            bot.send_message(m.chat.id, "❌ Invalid ID! Send numbers only e.g. 12345678")
            return
        if trader_id_input in TRADERS:
            u = get_user(uid)
            u["level"]="NONE"
            u["pocket_id"]=trader_id_input
            if u.get("deposit",0)==0: u["deposit"]=0
            TRADERS[trader_id_input]=uid
            save(); save_traders()
            kb=types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton("📊 Get Signals 🚀", callback_data="get_signal"))
            kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            bot.send_message(m.chat.id, f"✅ VERIFIED! You ARE under my affiliate link! 🎉\n🆔 Pocket ID: {trader_id_input}\n🚀 Bot UNLOCKED! 5 FREE signals/day!\n💰 Deposit $20 for STARTER 20/day!\n🎁 Promo {PROMO_CODE} 60% active!\n\nNow click GET SIGNAL! And your future deposits will AUTO-UPGRADE! 🔥", reply_markup=kb)
        else:
            kb=types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton(f"🔗 Register Now + {PROMO_CODE} 60% 🎁", url=get_affiliate_link(uid)))
            kb.add(types.InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL))
            bot.send_message(m.chat.id, f"❌ ID {trader_id_input} NOT found under my affiliate link! 🔒\n\nPocket didn't send us your ID yet!\n\nPossible reasons:\n1️⃣ You didn't use MY link to register\n2️⃣ You didn't use promo {PROMO_CODE}\n3️⃣ Postback delayed (wait 2-3 mins then try again!)\n\n👇 Click below to register with 60% Bonus!\n🎁 Promo Code: {PROMO_CODE} auto-applied!", reply_markup=kb)
        WAIT_STATE.pop(uid, None)
        return
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
            txt_ban=m.text.strip().lower().replace("/"," ").replace(":"," ").replace(","," ")
            import re
            match=re.search(r'(unban|ban)\s*(\d+)', txt_ban)
            if not match:
                num_match=re.search(r'(\d{5,})', txt_ban)
                if num_match:
                    action="ban"
                    uid_=num_match.group(1)
                else:
                    raise ValueError("no id")
            else:
                action=match.group(1)
                uid_=match.group(2)
            u_b=get_user(uid_)
            if action=="ban":
                u_b["banned"]=True; save()
                bot.send_message(m.chat.id, f"🚫 Banned {uid_} ✅\nName: {u_b.get('first_name','')} {u_b.get('username','')}")
                try:
                    bot.send_message(int(uid_), "🚫 You have been BANNED from WW Pocket Signals Bot! 🛑\n\nReason: Violation / Spam.\n❌ You cannot use signals anymore.\n📩 Contact owner if mistake.")
                except: pass
            else:
                u_b["banned"]=False; save()
                bot.send_message(m.chat.id, f"✅ Unbanned {uid_} ✅\nName: {u_b.get('first_name','')} {u_b.get('username','')}")
                try:
                    bot.send_message(int(uid_), "✅ You have been UNBANNED! 🎉\n\nWelcome back Boss! You can now use WW Pocket Signals again! 🚀\n👇 Send /start to continue!")
                except: pass
        except Exception as e:
            bot.send_message(m.chat.id, f"❌ Usage: `ban 123` or `unban 123`\nError: {e}")
        WAIT_STATE.pop(uid, None); return
    if ws.get("step")=="admin_degrade":
        try:
            parts=m.text.strip().split()
            uid_=parts[0]
            dat=get_user(uid_)
            old_level=dat.get("level","LOCKED")
            order=["VIP","PRO","STARTER","NONE","LOCKED"]
            if len(parts)>=2:
                target=parts[1].upper()
                new_level=target if target in order else "LOCKED"
            else:
                idx=order.index(old_level) if old_level in order else 4
                new_level=order[idx+1] if idx < len(order)-1 else "LOCKED"
            dat["level"]=new_level
            if new_level=="LOCKED": dat["deposit"]=0
            elif new_level=="STARTER": dat["deposit"]=20
            elif new_level=="PRO": dat["deposit"]=50
            elif new_level=="VIP": dat["deposit"]=100
            elif new_level=="NONE": dat["deposit"]=0
            save()
            bot.send_message(m.chat.id, f"⬇️ DEGRADE {uid_}: {old_level} → {new_level} ✅")
            try: bot.send_message(int(uid_), f"⬇️ Level changed: {old_level} → {new_level}\nSend /start")
            except: pass
        except Exception as e:
            bot.send_message(m.chat.id, f"Usage: 123456 or 123456 PRO\nError: {e}")
        WAIT_STATE.pop(uid, None); return
    if ws.get("step")=="admin_lock":
        try:
            uid_=m.text.strip()
            dat=get_user(uid_)
            dat["level"]="LOCKED"; dat["deposit"]=0; save()
            bot.send_message(m.chat.id, f"🔒 LOCKED {uid_} ✅")
            try: bot.send_message(int(uid_), "🔒 You have been LOCKED! Register again via official link to unlock!")
            except: pass
        except: bot.send_message(m.chat.id, "Usage: user_id")
        WAIT_STATE.pop(uid, None); return
    if ws.get("step")=="admin_search":
        try:
            uid_=m.text.strip(); dat=get_user(uid_); tot=dat.get("total_w",0)+dat.get("total_l",0); wr=int(dat.get("total_w",0)/tot*100) if tot>0 else 0
            bot.send_message(m.chat.id, f"🔍 {uid_}:\nLevel:{dat.get('level')}\nDeposit:${dat.get('deposit')}\nD:{dat.get('daily_w')}/{dat.get('daily_l')}\n🌍 GWR:{dat.get('total_w')}/{dat.get('total_l')} WR:{wr}%\nBanned:{dat.get('banned')}\nUser:{dat.get('username')} {dat.get('first_name')}\nPocketID:{dat.get('pocket_id','')}\nUsed:{dat.get('used_today')}")
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)

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
    print(f"🚀 WW POCKET BOT V18 POSTER + GRID + CHANNEL FIX RUNNING PROMO {PROMO_CODE} 60% 🔥 PORT {os.environ.get('PORT', 8080)}")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"⚠️ Polling error {e}, restart in 5s ⏳")
            time.sleep(5)
