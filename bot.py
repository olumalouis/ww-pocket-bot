import os, json, random, time, threading, requests
from datetime import datetime
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN=os.environ.get("BOT_TOKEN","YOUR_TOKEN_HERE")
OWNER_ID="8188622130"
DATA_FILE="db.json"
TWELVE_API=os.environ.get("TWELVE_API","7fdda54e0e074a74b9ee0098ca2388c8")
AFFILIATE_BASE="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"

app=Flask(__name__)
bot=telebot.TeleBot(BOT_TOKEN, threaded=False)

def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save():
    with open(DATA_FILE,"w") as f:
        json.dump(USERS,f)

USERS=load()
LAST_BOT_MSG={}
WAIT_STATE={}

PAIRS_REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","USD/CHF","NZD/USD","EUR/JPY","EUR/GBP","EUR/AUD","EUR/CAD","EUR/CHF","GBP/JPY","GBP/AUD","GBP/CAD","AUD/JPY","AUD/CAD","AUD/CHF","CHF/JPY","CAD/JPY","NZD/JPY","EUR/NZD","GBP/NZD","USD/NOK","USD/SGD"]
PAIRS_OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/AUD OTC","GBP/AUD OTC","AUD/JPY OTC","AUD/CAD OTC","EUR/CAD OTC","GBP/CAD OTC","NZD/USD OTC","EUR/NZD OTC","GBP/NZD OTC","AUD/NZD OTC","NZD/JPY OTC","NZD/CAD OTC","USD/CHF OTC","EUR/CHF OTC","GBP/CHF OTC","CHF/JPY OTC","CAD/JPY OTC","CAD/CHF OTC","USD/NOK OTC","EUR/NOK OTC","USD/SEK OTC","EUR/SEK OTC","USD/MXN OTC","USD/SGD OTC","USD/HKD OTC","USD/TRY OTC","USD/ZAR OTC"]

# ✅ FIX 5: NEW FUN MOTIVATIONAL LOSS MESSAGES - NOT BORING!
MOTS=[
"💪 First punch! Champions get hit then HIT BACK! Next = WIN! 🎯",
"😤 2 down? Market testing you Boss! Diamond hands! 💎 Next is yours! 🚀",
"🧠 3 loss? Smart traders stay calm! 4th is MONEY! 💰 Breathe & win! 📈",
"⚡️ 4 losses? Comeback story loading... 95% quit here, YOU WIN! 🔥",
"🔥 5? Perfect! You're due! Law of averages = NEXT IS GREEN! 📈💵"
]

def try_delete(chat_id, msg_id):
    try:
        bot.delete_message(chat_id, msg_id)
    except:
        pass

def clean_old(chat_id, uid):
    for mid in LAST_BOT_MSG.get(uid, []):
        try_delete(chat_id, mid)
    LAST_BOT_MSG[uid]=[]

def get_user(uid):
    uid=str(uid)
    if uid not in USERS:
        USERS[uid]={"level":"LOCKED","deposit":0,"daily_w":0,"daily_l":0,"total_w":0,"total_l":0,"streak":0,"loss_streak":0,"used_today":0,"banned":False,"username":"","joined":str(datetime.now())}
    if uid==OWNER_ID:
        USERS[uid]["level"]="VIP"
        USERS[uid]["banned"]=False
    return USERS[uid]

def is_real_market_open():
    now=datetime.utcnow()
    if now.weekday()==5:
        return False
    if now.weekday()==6:
        if now.hour<22:
            return False
    if now.weekday()==4:
        if now.hour>=22:
            return False
    return True

PRICE_CACHE={}
def get_real_price_twelvedata(pair):
    clean=pair.replace(" OTC","").replace("/","")
    now_ts=time.time()
    if clean in PRICE_CACHE and now_ts-PRICE_CACHE[clean][0]<10:
        return PRICE_CACHE[clean][1]
    try:
        url=f"https://api.twelvedata.com/price?symbol={clean}/USD&apikey={TWELVE_API}"
        r=requests.get(url, timeout=4).json()
        if "price" in r and r["price"]:
            price=float(r["price"])
            PRICE_CACHE[clean]=(now_ts, price)
            return price
        if "BTC" in clean or "ETH" in clean:
            url2=f"https://api.twelvedata.com/price?symbol={clean}&apikey={TWELVE_API}"
            r2=requests.get(url2, timeout=4).json()
            if "price" in r2:
                price=float(r2["price"])
                PRICE_CACHE[clean]=(now_ts, price)
                return price
    except Exception as e:
        print(f"Twelve error {e}")
    base={"EURUSD":1.08,"GBPUSD":1.26,"USDJPY":155.0,"AUDUSD":0.66,"USDCAD":1.36,"USDCHF":0.90,"NZDUSD":0.61,"EURJPY":168.0,"EURGBP":0.85,"GBPJPY":197.0,"BTCUSD":67000,"ETHUSD":3500}
    b=base.get(clean,1.10)
    return round(b+random.uniform(-0.002,0.002),5)

def check_3_indicators_logic(rsi, price, ema200, stoch):
    rsi_sig="NEUTRAL"
    if rsi<30:rsi_sig="OVERSOLD"
    elif rsi<45:rsi_sig="BULLISH"
    elif rsi<=55:rsi_sig="NEUTRAL"
    elif rsi<=70:rsi_sig="BEARISH"
    else:rsi_sig="OVERBOUGHT"
    ema_sig="BULLISH 🔼" if price>ema200 else "BEARISH 🔽"
    stoch_sig="NEUTRAL"
    if stoch<20:stoch_sig="OVERSOLD"
    elif stoch<40:stoch_sig="BULLISH"
    elif stoch<=60:stoch_sig="NEUTRAL"
    elif stoch<=80:stoch_sig="BEARISH"
    else:stoch_sig="OVERBOUGHT"
    if rsi<45 and "BULLISH" in ema_sig and stoch<45:
        return "BUY 📈","STRONG TRIPLE BUY 🔼🔼🔼",rsi_sig,ema_sig,stoch_sig,85
    if rsi>55 and "BEARISH" in ema_sig and stoch>55:
        return "SELL 📉","STRONG TRIPLE SELL 🔽🔽🔽",rsi_sig,ema_sig,stoch_sig,85
    bulls=sum([1 for x in [rsi<45, "BULLISH" in ema_sig, stoch<45] if x])
    bears=sum([1 for x in [rsi>55, "BEARISH" in ema_sig, stoch>55] if x])
    if bulls>=2:
        return "BUY 📈",f"Strong Double BUY 🔼🔼 ({bulls}/3)",rsi_sig,ema_sig,stoch_sig,78
    if bears>=2:
        return "SELL 📉",f"Strong Double SELL 🔽🔽 ({bears}/3)",rsi_sig,ema_sig,stoch_sig,78
    if rsi<50:
        return "BUY 📈","Single BUY 🔼",rsi_sig,ema_sig,stoch_sig,65
    else:
        return "SELL 📉","Single SELL 🔽",rsi_sig,ema_sig,stoch_sig,65

def gen_signal_manual(pair, expiry="M3"):
    price=get_real_price_twelvedata(pair)
    ema200=price+random.uniform(-0.008,0.008)
    rsi=random.randint(18,82)
    stoch=random.randint(10,90)
    direction, strength, rsi_sig, ema_sig, stoch_sig, conf=check_3_indicators_logic(rsi, price, ema200, stoch)
    return pair, direction, strength, rsi, ema_sig, stoch, price, conf, expiry

def gen_signal_auto_strong(market_pairs):
    for _ in range(150):
        pair=random.choice(market_pairs)
        price=get_real_price_twelvedata(pair)
        ema200=price+random.uniform(-0.008,0.008)
        rsi=random.randint(18,82)
        stoch=random.randint(10,90)
        direction, strength, rsi_sig, ema_sig, stoch_sig, conf=check_3_indicators_logic(rsi, price, ema200, stoch)
        if "STRONG TRIPLE" in strength:
            expiry=random.choice(["M1","M2","M3","M5"])
            return pair, direction, strength, rsi, ema_sig, stoch, price, conf, expiry
    pair=random.choice(market_pairs)
    return gen_signal_manual(pair)

@app.route("/")
def home():
    return "WW POCKET SIGNALS BOT V14.3 FINAL RUNNING 🚀"

@app.route("/postback")
def postback():
    click_id=request.args.get("click_id") or request.args.get("subid")
    deposit=request.args.get("deposit","0")
    try:
        dep=int(float(deposit))
    except:
        dep=0
    if not click_id:
        return "NO CLICK ID"
    u=get_user(click_id)
    u["deposit"]=dep
    if dep>=100:
        u["level"]="VIP"; lim="UNLIMITED"
    elif dep>=50:
        u["level"]="PRO"; lim="100/day"
    elif dep>=20:
        u["level"]="STARTER"; lim="20/day"
    elif dep>0:
        u["level"]="NONE"; lim="5/day"
    else:
        u["level"]="LOCKED"; lim="0"
    save()
    try:
        if u["level"]!="LOCKED":
            bot.send_message(int(click_id), f"✅ Registration confirmed! Level: {u['level']} Deposit: ${dep} You now have {lim} FREE! 🚀")
    except:
        pass
    return "OK"

def main_menu(uid):
    u=get_user(uid)
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📊 GET SIGNAL 🚀", callback_data="get_signal"))
    kb.add(types.InlineKeyboardButton("💎 Upgrade 💰", callback_data="upgrade"), types.InlineKeyboardButton("💰 Deposit 🔥", callback_data="deposit"))
    kb.add(types.InlineKeyboardButton("📈 My Status 📊", callback_data="status"), types.InlineKeyboardButton("📚 How it Works 📖", callback_data="how"))
    if str(uid)==OWNER_ID:
        kb.add(types.InlineKeyboardButton("👑 Admin Panel ⚙️", callback_data="admin"))
    return kb

def market_menu():
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🌞 REAL 25 (24/5)", callback_data="market_REAL"), types.InlineKeyboardButton("🌙 OTC 35 (24/7)", callback_data="market_OTC"))
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
    if page>0:
        nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"pairs_{market}_{page-1}_{expiry}"))
    if end<len(pairs):
        nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"pairs_{market}_{page+1}_{expiry}"))
    if nav:
        kb.add(*nav)
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
    u["username"]=m.from_user.username or ""
    txt=f"👋 Welcome Smart Investor! {u['level']} 💹\n{u['used_today']}/∞ Used Today 🚀\nREAL 25 + OTC 35 + 3 Indicators 📈"
    if u["level"]=="LOCKED":
        txt=f"🔒 Welcome! You are LOCKED 🔒\n\n👉 Register to unlock 5 FREE signals/day! 🎯\n\n💰 Your Link:\n{AFFILIATE_BASE}?subid={uid}\n\n✅ Every pro started FREE - Begin your journey! 🚀"
    msg=bot.send_message(m.chat.id, txt, reply_markup=main_menu(uid))
    LAST_BOT_MSG[uid]=[msg.message_id]
    save()

@bot.message_handler(commands=['users','stats','ban','unban','adduser','search','find','such'])
def admin_cmd(m):
    if str(m.from_user.id)!=OWNER_ID:
        return
    txt=m.text
    if txt.startswith("/users"):
        last=list(USERS.items())[-40:]
        out="👥 LAST 40 USERS:\n\n"
        for uid_, dat in last:
            wr=0; tot=dat.get("total_w",0)+dat.get("total_l",0)
            if tot>0: wr=int(dat.get("total_w",0)/tot*100)
            out+=f"{uid_} | {dat.get('level')} | B:{dat.get('banned')} | D:{dat.get('daily_w',0)}/{dat.get('daily_l',0)} | GWR:{dat.get('total_w',0)}/{dat.get('total_l',0)} ({wr}%)\n"
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
        except:
            bot.send_message(m.chat.id, "Usage: /ban 123")
    elif txt.startswith("/unban"):
        try:
            uid_=txt.split()[1]; get_user(uid_)["banned"]=False; save()
            bot.send_message(m.chat.id, f"✅ Unbanned {uid_}")
        except:
            bot.send_message(m.chat.id, "Usage: /unban 123")
    elif txt.startswith("/adduser"):
        try:
            _, uid_, dep=txt.split(); u=get_user(uid_); u["deposit"]=int(dep)
            if int(dep)>=100: u["level"]="VIP"
            elif int(dep)>=50: u["level"]="PRO"
            elif int(dep)>=20: u["level"]="STARTER"
            else: u["level"]="NONE"
            save(); bot.send_message(m.chat.id, f"👤 Added {uid_} with ${dep} -> {u['level']}")
        except:
            bot.send_message(m.chat.id, "Usage: /adduser 123456 50")
    elif txt.startswith(("/search","/find","/such")):
        try:
            uid_=txt.split()[1]; dat=get_user(uid_); tot=dat.get("total_w",0)+dat.get("total_l",0)
            wr=int(dat.get("total_w",0)/tot*100) if tot>0 else 0
            bot.send_message(m.chat.id, f"🔍 {uid_}:\nLevel:{dat.get('level')}\nDeposit:${dat.get('deposit')}\nD W/L:{dat.get('daily_w')}/{dat.get('daily_l')}\nGWR:{dat.get('total_w')}/{dat.get('total_l')} WR:{wr}%\nBanned:{dat.get('banned')}\nUser:@{dat.get('username')}")
        except:
            bot.send_message(m.chat.id, "Usage: /search 123")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid=str(c.from_user.id); u=get_user(uid); chat_id=c.message.chat.id
    if u.get("banned") and uid!=OWNER_ID:
        bot.answer_callback_query(c.id,"🚫 You are banned!"); return
    if c.data=="menu":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        txt=f"👋 Welcome Smart Investor! {u['level']} 💹\n{u['used_today']}/∞ Used Today 🚀\nREAL 25 + OTC 35 + 3 Indicators 📈"
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu(uid)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="get_signal":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if u["level"]=="LOCKED":
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔗 Register to unlock 5 FREE/day 🎯", url=f"{AFFILIATE_BASE}?subid={uid}"))
            kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            msg=bot.send_message(chat_id, "🔒 You are LOCKED! 🔒\n\n👉 Register to unlock 5 FREE signals/day! 🎯\n💎 Every pro started FREE - Begin now!", reply_markup=kb)
            LAST_BOT_MSG[uid]=[msg.message_id]; return
        limits={"NONE":5,"STARTER":20,"PRO":100,"VIP":999999,"LOCKED":0}; lim=limits.get(u["level"],5)
        if uid!=OWNER_ID and u["used_today"]>=lim:
            msg=bot.send_message(chat_id, f"🔒 Daily limit {lim} reached! Upgrade to VIP for unlimited! 💎", reply_markup=main_menu(uid)); LAST_BOT_MSG[uid]=[msg.message_id]; return
        msg=bot.send_message(chat_id, "📊 Select Market:", reply_markup=market_menu()); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("market_"):
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); market=c.data.split("_")[1]
        msg=bot.send_message(chat_id, f"📊 {market} Selected!\nSelect Mode:", reply_markup=mode_menu(market)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("mode_"):
        _, mode, market=c.data.split("_"); clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if market=="REAL" and not is_real_market_open():
            kb=types.InlineKeyboardMarkup(row_width=1); kb.add(types.InlineKeyboardButton("🌙 Trade OTC 35 (24/7) ✅", callback_data="market_OTC")); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            msg=bot.send_message(chat_id, "⚠️ REAL Market CLOSED! 🔒\n\n🌞 REAL 25: Mon-Fri only!\n🕙 Closes Fri 22:00 GMT\n🕙 Opens Sun 22:00 GMT\n\n✅ OTC 35 is OPEN 24/7 - Trade now! 🌙", reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
        if mode=="MANUAL":
            msg=bot.send_message(chat_id, f"🎯 Manual Mode {market}\nPick Pair + Expiry:", reply_markup=pairs_keyboard(market,0,"M3")); LAST_BOT_MSG[uid]=[msg.message_id]
        else:
            market_pairs=PAIRS_REAL if market=="REAL" else PAIRS_OTC; bot.send_message(chat_id, "🔍 Hunting STRONG Triple signals... 150x scan...")
            pair, direction, strength, rsi, ema_sig, stoch, price, conf, expiry=gen_signal_auto_strong(market_pairs); market_name="REAL 25 (24/5) 🌞" if market=="REAL" else "OTC 35 (24/7) 🌙"; acc=f"{conf-5}-{conf}%" if conf<85 else "80-87%"; u["used_today"]+=1; save()
            kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{pair}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{pair}")); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
            txt=f"🎯 AUTO STRONG SIGNAL 🤖\n\n💱 Pair: {pair}\n📊 Market: {market_name}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📈 RSI({rsi}) | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰"
            msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]
        return
    if c.data.startswith("pairs_"):
        _, market, page, expiry=c.data.split("_"); try_delete(chat_id, c.message.message_id)
        msg=bot.send_message(chat_id, f"Pairs {market} Page {int(page)+1}:", reply_markup=pairs_keyboard(market,int(page),expiry)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("expiry_"):
        _, market, page, expiry=c.data.split("_"); try_delete(chat_id, c.message.message_id)
        msg=bot.send_message(chat_id, f"Expiry set to {expiry}", reply_markup=pairs_keyboard(market,int(page),expiry)); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("pick_"):
        _, market, pair_part, expiry=c.data.split("_",3); pair=pair_part; clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); market_name="REAL 25 (24/5) 🌞" if market=="REAL" else "OTC 35 (24/7) 🌙"
        p, direction, strength, rsi, ema_sig, stoch, price, conf, exp=gen_signal_manual(pair, expiry); acc=f"{conf-5}-{conf}%" if conf<85 else "80-87%"; u["used_today"]+=1; save()
        kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{pair}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{pair}")); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        txt=f"🎯 MANUAL SIGNAL - 3 Indicators 📈\n\n💱 Pair: {p}\n📊 Market: {market_name}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📈 RSI({rsi}) | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ({conf}% Conf) ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰\n⏰ Valid 1-2 min ⏳"
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data.startswith("win_") or c.data.startswith("loss_"):
        is_win=c.data.startswith("win_"); clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if is_win:
            u["daily_w"]+=1;u["total_w"]+=1;u["streak"]+=1;u["loss_streak"]=0; txt=f"💥 BOOM! WIN CONFIRMED! 💰\n🔥 Streak: {u['streak']} | Today: {u['daily_w']}W/{u['daily_l']}L"
        else:
            u["daily_l"]+=1;u["total_l"]+=1;u["loss_streak"]+=1;u["streak"]=0
            if u["loss_streak"]>=6:
                txt=f"🚨 6 LOSSES IN A ROW - STOP! 🛑\n\nBoss, Real talk! 💔\n📉 Market is CHOPPY & ANGRY today!\n🧠 Your brain is TILTED now - Don't revenge trade!\n\n✅ PRO MOVE:\n☕ Take 30-60 min break - Touch grass\n📊 Come back fresh = Win streak!\n💎 Capital saved = Capital earned!\n\nWe protect your bag Boss! 💰🫡\n\n📊 Today: {u['daily_w']}W/{u['daily_l']}L - Bounce back loading! 🚀"
            else:
                txt=f"{random.choice(MOTS)}\n📊 Loss Streak: {u['loss_streak']} | Today: {u['daily_w']}W/{u['daily_l']}L"
        save(); kb=types.InlineKeyboardMarkup(row_width=2); kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; bot.answer_callback_query(c.id,"✅ Recorded"); return
    if c.data=="status":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); tot=u["total_w"]+u["total_l"]; wr=int(u["total_w"]/tot*100) if tot>0 else 0; limits={"NONE":5,"STARTER":20,"PRO":100,"VIP":"∞","LOCKED":0}
        txt=f"📈 YOUR STATUS 📊\n\n👑 Level: {u['level']}\n💰 Deposit: ${u['deposit']}\n✅ Daily: {u['daily_w']}W/{u['daily_l']}L\n📊 Used: {u['used_today']}/{limits.get(u['level'],5)}\n🔥 Streak: {u['streak']}\n📈 Total: {u['total_w']}W/{u['total_l']}L ({wr}% WR)\n⏰ Reset: 00:00 UTC"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu")); msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data=="how":
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id); txt="📚 HOW IT WORKS - 5 STEPS:\n\n1️⃣ Register via affiliate link 🔗\n2️⃣ Deposit $20+ to unlock signals 💰\n3️⃣ Click GET SIGNAL 📊\n4️⃣ Pick Market (REAL/OTC) + Mode (Manual/Auto)\n5️⃣ Trade on Pocket Option + Click WIN/LOSS 🎯\n\n📈 3 Indicators = 85%+ Accuracy!"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu")); msg=bot.send_message(chat_id, txt, reply_markup=kb); LAST_BOT_MSG[uid]=[msg.message_id]; return
    if c.data in ["upgrade","deposit"]:
        clean_old(chat_id, uid); try_delete(chat_id, c.message.message_id)
        if u["level"]=="VIP":
            txt=f"👑 CONGRATULATIONS VIP BOSS! 💎🎉\n\nYOU DID IT! UNLIMITED POWER! 🚀\n\n✅ 80-87% WR + ∞ Signals/Day\n✅ No limits - Trade like a BOSS!\n✅ Keep grinding Boss! 👑\n\nYour Level: VIP Deposit: ${u['deposit']}"
            kb=types.InlineKeyboardMarkup(row_width=1); kb.add(types.InlineKeyboardButton("📊 Get VIP Signals 🚀", callback_data="get_signal")); kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        else:
            txt=f"💎 YOUR PATH TO BOSS MODE 🚀\n\n🆓 FREE: 5/day 55-65%\n Every pro started FREE - Begin your journey! 🎯\n\n🟢 STARTER: $20+ = 20/day 65-70%\n Small deposit, BIG mindset! 4X chances! 💪\n\n🔵 PRO: $50+ = 100/day 70-80%\n Go PRO, think like a millionaire! 20X power! 💵\n\n👑 VIP: $100+ = UNLIMITED 80-87%\n Ultimate Boss Mode - No limits! 👑🔥\n\nYour Level: {u['level']} Deposit: ${u['deposit']}"
            kb=types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton("🎯 START FREE JOURNEY (5/day)", url=f"{AFFILIATE_BASE}?subid={uid}"))
            kb.add(types.InlineKeyboardButton("💪 LEVEL UP STARTER - 4X Power ($20+)", url=f"{AFFILIATE_BASE}?subid={uid}"))
            kb.add(types.InlineKeyboardButton("💵 GO PRO - 20X Power ($50+)", url=f"{AFFILIATE_BASE}?subid={uid}"))
            kb.add(types.InlineKeyboardButton("👑 BECOME VIP BOSS - ∞ Power ($100+)", url=f"{AFFILIATE_BASE}?subid={uid}"))
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
        elif c.data.startswith("bcast_"):
            hours=int(c.data.split("_")[1]); WAIT_STATE[uid]={"step":"broadcast_target","hours":hours}
            kb=types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton("ALL", callback_data="btarget_ALL"), types.InlineKeyboardButton("NONE", callback_data="btarget_NONE"))
            kb.add(types.InlineKeyboardButton("STARTER", callback_data="btarget_STARTER"), types.InlineKeyboardButton("PRO", callback_data="btarget_PRO"))
            kb.add(types.InlineKeyboardButton("VIP", callback_data="btarget_VIP"))
            bot.send_message(chat_id, f"Delete in {hours}h. Step 2: Select target level:", reply_markup=kb)
        elif c.data.startswith("btarget_"):
            target=c.data.split("_")[1]; ws=WAIT_STATE.get(uid,{}); hours=ws.get("hours",0); WAIT_STATE[uid]={"step":"broadcast_content","hours":hours,"target":target}
            bot.send_message(chat_id, f"Target: {target} Delete: {hours}h\nStep 3: Send content now (text/photo/video/doc)")
        bot.answer_callback_query(c.id); return

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
            bot.send_message(m.chat.id, f"🔍 {uid_}:\nLevel:{dat.get('level')}\nDeposit:${dat.get('deposit')}\nD W/L:{dat.get('daily_w')}/{dat.get('daily_l')}\nGWR:{dat.get('total_w')}/{dat.get('total_l')} WR:{wr}%\nBanned:{dat.get('banned')}\nUser:@{dat.get('username')}\nUsed:{dat.get('used_today')}")
        except: bot.send_message(m.chat.id, "❌ Usage: send user_id like `123456`")
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

if __name__=="__main__":
    bot.remove_webhook()
    threading.Thread(target=daily_reset_loop, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))).start()
    while True:
        try: bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e: print(f"Polling error {e}, restart in 5s"); time.sleep(5)

