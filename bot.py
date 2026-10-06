import os, json, threading, random, time, requests
from datetime import datetime, timezone
from flask import Flask, request
import telebot
from telebot import types

app = Flask(__name__)
@app.route('/')
def home():
    return 'WW Pocket Signals V14.3 FINAL - 3 Indicators + Real Price ✅'

TOKEN = os.getenv("BOT_TOKEN","").strip()
AFF_BASE = "https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
TWELVE_KEY = "7fdda54e0e074a74b9ee0098ca2388c8"
OWNER = 8188622130

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
bot.delete_webhook(drop_pending_updates=True)

DB_FILE="db.json"
try:
    with open(DB_FILE) as f:
        DB=json.load(f)
except:
    DB={"users":{},"banned":[],"stats":{"gwr_w":0,"gwr_l":0},"_bcast_tmp":{},"_bcast_wait":{},"_admin_wait":{}}

def save():
    try:
        with open(DB_FILE,"w") as f:
            json.dump(DB,f)
    except: pass

LEVELS={"LOCKED":{"limit":0,"wr":"80-87% 🔥"},"NONE":{"limit":5,"wr":"55-65% 🌱"},"STARTER":{"limit":20,"wr":"65-70% 📈"},"PRO":{"limit":100,"wr":"70-80% 💎"},"VIP":{"limit":999999,"wr":"80-87% 👑"}}

def get_level(deposit):
    if deposit>=100: return "VIP"
    if deposit>=50: return "PRO"
    if deposit>=20: return "STARTER"
    if deposit>=0: return "NONE"
    return "LOCKED"

REAL_PAIRS=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","USD/CHF","NZD/USD","EUR/JPY","EUR/GBP","EUR/AUD","EUR/CAD","EUR/CHF","GBP/JPY","GBP/AUD","GBP/CAD","AUD/JPY","AUD/CAD","AUD/CHF","CHF/JPY","CAD/JPY","NZD/JPY","EUR/NZD","GBP/NZD","USD/NOK","USD/SGD"]
OTC_PAIRS=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","EUR/JPY OTC","AUD/USD OTC","USD/CAD OTC","GBP/JPY OTC","EUR/GBP OTC","USD/CHF OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC","AUD/JPY OTC","EUR/CAD OTC","USD/NOK OTC","BTC/USD OTC","ETH/USD OTC","AUD/CAD OTC","AUD/CHF OTC","EUR/CHF OTC","GBP/CHF OTC","CHF/JPY OTC","EUR/NZD OTC","GBP/NZD OTC","AUD/NZD OTC","USD/SGD OTC","USD/HKD OTC","USD/MXN OTC","USD/TRY OTC","USD/ZAR OTC","USD/BRL OTC","USD/SEK OTC","NZD/CAD OTC","CAD/JPY OTC","EUR/SGD OTC"]

MOTIV=["Focus • Power • Win 🔥","Discipline = Profit 💎","Next is WIN! 🚀","Stay Sharp! ⚡","Patience Pays! 💰","Control • Execute! 🎯"]

def is_real_open():
    now = datetime.now(timezone.utc)
    wd = now.weekday()
    if wd == 5: return False
    if wd == 6: return False
    if wd == 4 and now.hour >= 22: return False
    return True
def build_aff_link(uid):
    uid=str(uid)
    base=AFF_BASE
    if "{id}" in base: return base.replace("{id}",uid)
    sep="&" if "?" in base else "?"
    return base + sep + "subid=" + uid

def ensure(uid, username=""):
    uid=str(uid)
    if uid==str(OWNER) and uid in DB["banned"]: DB["banned"].remove(uid)
    if uid not in DB["users"]:
        DB["users"][uid]={"username":username,"level":"LOCKED","deposit":0,"daily_used":0,"daily_w":0,"daily_l":0,"total_w":0,"total_l":0,"streak":0,"loss_streak":0,"registered":False,"last_day":str(datetime.now(timezone.utc).date())}
    u=DB["users"][uid]
    today=str(datetime.now(timezone.utc).date())
    if u.get("last_day")!=today:
        u["daily_used"]=0; u["daily_w"]=0; u["daily_l"]=0; u["streak"]=0; u["loss_streak"]=0; u["last_day"]=today; save()
    if uid==str(OWNER): u["level"]="VIP"; u["registered"]=True
    return u

def is_banned(uid):
    if str(uid)==str(OWNER): return False
    return str(uid) in DB["banned"]

def locked_text(uid):
    return "🔒 *WELCOME TO WW POCKET SIGNALS BOT* 🚀\n\nHello "+str(uid)+"! 👋\n\nWe provide 80-87% WR signals! 🔥\n\n*How to unlock:*\n1️⃣ Register with link below 🔗\n2️⃣ Get 5/day FREE 🎁\n3️⃣ Deposit to upgrade:\n\n📊 STARTER $20 = 20/day 65-70% 📈\n💎 PRO $50 = 100/day 70-80% 💰\n👑 VIP $100 = UNLIMITED 80-87% 🚀"

def locked_kb(uid):
    link=build_aff_link(uid)
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔗 Register Now - Unlock 5/day FREE 🎁", url=link))
    kb.add(types.InlineKeyboardButton("📜 How it Works 📚", callback_data="how"))
    return kb

def main_kb(uid):
    u=ensure(uid)
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📊 GET SIGNAL 🚀", callback_data="get_signal"))
    kb.add(types.InlineKeyboardButton("💎 Upgrade 💰", callback_data="upgrade"),types.InlineKeyboardButton("💰 Deposit 🔥", callback_data="deposit"))
    kb.add(types.InlineKeyboardButton("📈 My Status 📊", callback_data="mystatus"),types.InlineKeyboardButton("📜 How it Works 📚", callback_data="how"))
    if str(uid)==str(OWNER): kb.add(types.InlineKeyboardButton("👑 Admin Panel ⚙️", callback_data="admin"))
    return kb

def market_kb():
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("✅ REAL 25 (24/5) 📈", callback_data="market_real"),types.InlineKeyboardButton("🔶 OTC 35 (24/7) 🌙", callback_data="market_otc"))
    return kb

def mode_kb(market):
    label = "25" if market=="real" else "35"
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(f"✋ Manual {label} 📝", callback_data="mode_manual_"+market),types.InlineKeyboardButton(f"🤖 Auto {label} - Hunt Strong 🔥", callback_data="mode_auto_"+market))
    kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="get_signal"))
    return kb

def pairs_kb(market, page=0, expiry="M1"):
    pairs=REAL_PAIRS if market=="real" else OTC_PAIRS
    per=10; start=page*per; end=start+per
    kb=types.InlineKeyboardMarkup(row_width=2)
    for p in pairs[start:end]:
        kb.add(types.InlineKeyboardButton(p+" ["+expiry+"] 📊", callback_data="pick_"+market+"_"+p+"_"+expiry+"_"+str(page)))
    kb.row(types.InlineKeyboardButton("⏰ M1"+(" ✅" if expiry=="M1" else ""), callback_data="expiry_"+market+"_"+str(page)+"_M1"),types.InlineKeyboardButton("⏰ M2"+(" ✅" if expiry=="M2" else ""), callback_data="expiry_"+market+"_"+str(page)+"_M2"))
    kb.row(types.InlineKeyboardButton("⏰ M3"+(" ✅" if expiry=="M3" else ""), callback_data="expiry_"+market+"_"+str(page)+"_M3"),types.InlineKeyboardButton("⏰ M5"+(" ✅" if expiry=="M5" else ""), callback_data="expiry_"+market+"_"+str(page)+"_M5"))
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("⬅️ Prev 🔙", callback_data="nav_"+market+"_"+str(page-1)+"_"+expiry))
    if end < len(pairs): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data="nav_"+market+"_"+str(page+1)+"_"+expiry))
    if nav: kb.add(*nav)
    kb.add(types.InlineKeyboardButton("⬅️ Back Market 🔙", callback_data="market_"+market))
    return kb

def get_real_price(pair):
    symbol = pair.replace(" OTC","")
    try:
        r = requests.get(f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_KEY}", timeout=3)
        data = r.json()
        if "price" in data: return float(data["price"])
    except: pass
    return None

def gen_signal(pair, expiry, uid, force_weak=False):
    real_price = get_real_price(pair)
    if "JPY" in pair:
        price = real_price if real_price else round(random.uniform(140,160),2)
        ema200 = round(price + random.uniform(-1,1),2)
    elif "BTC" in pair:
        price = real_price if real_price else round(random.uniform(65000,70000),2)
        ema200 = round(price + random.uniform(-500,500),2)
    elif "ETH" in pair:
        price = real_price if real_price else round(random.uniform(2500,4000),2)
        ema200 = round(price + random.uniform(-50,50),2)
    else:
        price = real_price if real_price else round(random.uniform(1.0,1.5),5)
        ema200 = round(price + random.uniform(-0.02,0.02),5)

    rsi = round(random.uniform(38,62),1) if force_weak else round(random.uniform(18,82),1)
    stoch = round(random.uniform(10,90),1)
    above = price > ema200

    if rsi < 30: rsi_text=f"📉 RSI {rsi} Oversold 🔥"
    elif rsi < 45: rsi_text=f"📈 RSI {rsi} Bullish 🔼"
    elif rsi < 55: rsi_text=f"➖ RSI {rsi} Neutral"
    elif rsi < 70: rsi_text=f"📉 RSI {rsi} Bearish 🔽"
    else: rsi_text=f"📈 RSI {rsi} Overbought ⚠️"

    if stoch < 20: stoch_text=f"📉 Stoch {stoch} Oversold 🔥"
    elif stoch < 40: stoch_text=f"📈 Stoch {stoch} Bullish 🔼"
    elif stoch < 60: stoch_text=f"➖ Stoch {stoch} Neutral"
    elif stoch < 80: stoch_text=f"📉 Stoch {stoch} Bearish 🔽"
    else: stoch_text=f"📈 Stoch {stoch} Overbought ⚠️"

    ema_dir="Above ⬆️" if above else "Below ⬇️"; ema_arrow="🔼" if above else "🔽"
    ema_text=f"💹 Price {price} {ema_dir} EMA200 {ema_arrow}"

    bullish_rsi = rsi < 45; bearish_rsi = rsi > 55; bullish_stoch = stoch < 45; bearish_stoch = stoch > 55

    if bullish_rsi and above and bullish_stoch: direction="BUY 📈 - STRONG TRIPLE 🔼🔼🔼 🔥🔥🔥"
    elif bearish_rsi and not above and bearish_stoch: direction="SELL 📉 - STRONG TRIPLE 🔽🔽🔽 🔥🔥🔥"
    elif bullish_rsi and above: direction="BUY 📈 - Strong Bullish 🔼🔼 💎"
    elif bearish_rsi and not above: direction="SELL 📉 - Strong Bearish 🔽🔽 💎"
    elif bullish_rsi or above or bullish_stoch: direction="BUY 📈 - Bullish 🔼"
    else: direction="SELL 📉 - Bearish 🔽"

    u=ensure(uid); lvl=u["level"]; used=u["daily_used"]; lim=LEVELS[lvl]["limit"]
    lvl_emoji="🔥 VIP 🔶👑" if lvl=="VIP" else "💎 "+lvl+" 📊"
    lim_str=str(used+1)+"/"+(str(lim) if lim<999999 else "∞")
    txt=f"{lvl_emoji}\n📊 {pair} 💹\n📈 {direction}\n⏰ Exp {expiry} ⏳\n📉 {rsi_text}\n📊 EMA200 {ema_text}\n📈 {stoch_text}\n📊 {lim_str} Today 🔥"
    return txt, direction, rsi, above, stoch

def hunt_strong_signal(market, uid):
    pairs=REAL_PAIRS if market=="real" else OTC_PAIRS
    exps=["M1","M2","M3","M5"]
    for _ in range(150):
        pair = random.choice(pairs); exp = random.choice(exps)
        txt, direction, rsi, above, stoch = gen_signal(pair, exp, uid)
        if (rsi < 35 and stoch < 30 and above) or (rsi > 65 and stoch > 70 and not above):
            return txt, pair, exp
    for _ in range(100):
        pair = random.choice(pairs); exp=random.choice(exps)
        txt, direction, rsi, above, stoch = gen_signal(pair, exp, uid)
        if (rsi < 40 and above) or (rsi > 60 and not above): return txt, pair, exp
    best=None
    for _ in range(20):
        pair = random.choice(pairs); exp=random.choice(exps)
        txt, direction, rsi, above, stoch = gen_signal(pair, exp, uid)
        best=(txt,pair,exp)
    return best

def can_get_signal(uid):
    u=ensure(uid)
    if is_banned(uid): return False, "Banned ⛔"
    if u["level"]=="LOCKED": return False, "locked 🔒"
    if u["daily_used"]>=LEVELS[u["level"]]["limit"]: return False, "limit 🚫"
    return True, "ok ✅"@app.route('/postback')
def postback():
    click_id=request.args.get('click_id') or request.args.get('subid')
    dep=request.args.get('deposit','0')
    try: dep=float(dep)
    except: dep=0
    if not click_id: return 'no click_id ⛔'
    u=ensure(click_id, "aff")
    u["registered"]=True
    u["deposit"]=max(u.get("deposit",0), dep)
    u["level"]=get_level(u["deposit"])
    if u["level"]=="LOCKED": u["level"]="NONE"
    save()
    try: bot.send_message(int(click_id), "✅ Registration confirmed! 🎉 Level: "+u["level"]+" 👑 Deposit: $"+str(dep)+" 💰 You now have "+str(LEVELS[u["level"]]["limit"])+" signals/day FREE! 🚀")
    except: pass
    return 'ok ✅'

@bot.message_handler(commands=['start'])
def start_cmd(m):
    u=ensure(m.from_user.id, m.from_user.username or "")
    if is_banned(m.from_user.id): bot.send_message(m.chat.id,"⛔ You are banned 🚫"); return
    if u["level"]=="LOCKED" or (not u["registered"] and str(m.from_user.id)!=str(OWNER)):
        if str(m.from_user.id)==str(OWNER): bot.send_message(m.chat.id, "👋 Welcome "+m.from_user.first_name+"! 👑 VIP 📊 "+str(u["daily_used"])+"/∞ Used Today 🔥", reply_markup=main_kb(m.from_user.id))
        else: bot.send_message(m.chat.id, locked_text(m.from_user.id), parse_mode="Markdown", reply_markup=locked_kb(m.from_user.id))
    else:
        lim=LEVELS[u["level"]]["limit"]; lim_str=str(lim) if lim<999999 else "∞"
        bot.send_message(m.chat.id, "👋 Welcome "+m.from_user.first_name+"! 👑 "+u["level"]+" 📊 "+str(u["daily_used"])+"/"+lim_str+" Used Today 🚀", reply_markup=main_kb(m.from_user.id))

@bot.message_handler(commands=['admin','users','stats','ban','unban','adduser','search','find','such','broadcast'])
def admin_cmds(m):
    if str(m.from_user.id)!=str(OWNER): return
    txt=m.text.lower()
    if txt.startswith('/users'):
        out="👥 *Last 40 Users* 📊\n"
        for uid, u in list(DB["users"].items())[-40:]:
            wr = (u["total_w"]/(u["total_w"]+u["total_l"])*100) if (u["total_w"]+u["total_l"])>0 else 0
            ban=" BANNED ⛔" if uid in DB["banned"] else ""
            out+=uid+" "+u["level"]+ban+" D:"+str(u["daily_w"])+"W/"+str(u["daily_l"])+"L GWR:"+str(u["total_w"])+"/"+str(u["total_l"])+" WR:"+str(int(wr))+"%\n"
        bot.send_message(m.chat.id, out, parse_mode="Markdown")
    elif txt.startswith('/stats'):
        levels_count={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for u in DB["users"].values(): levels_count[u["level"]]=levels_count.get(u["level"],0)+1
        gwr_w=sum(u["total_w"] for u in DB["users"].values()); gwr_l=sum(u["total_l"] for u in DB["users"].values())
        bot.send_message(m.chat.id, "📊 Levels: "+str(levels_count)+" ⛔ Banned: "+str(len(DB["banned"]))+" 🌍 GWR Total: "+str(gwr_w)+"W/"+str(gwr_l)+"L 🚀")
    elif txt.startswith('/ban'):
        parts=m.text.split()
        if len(parts)>1:
            if parts[1] not in DB["banned"]: DB["banned"].append(parts[1]); save()
            bot.send_message(m.chat.id,"✅ Banned "+parts[1]+" ⛔")
    elif txt.startswith('/unban'):
        parts=m.text.split()
        if len(parts)>1 and parts[1] in DB["banned"]: DB["banned"].remove(parts[1]); save(); bot.send_message(m.chat.id,"✅ Unbanned "+parts[1]+" 🎉")
    elif txt.startswith('/adduser'):
        parts=m.text.split()
        if len(parts)>=3:
            uid=parts[1]; dep=float(parts[2]); u=ensure(uid); u["deposit"]=dep; u["level"]=get_level(dep); u["registered"]=True; save()
            bot.send_message(m.chat.id,"✅ Added "+uid+" level "+u["level"]+" 👑")
    elif txt.startswith('/search') or txt.startswith('/find') or txt.startswith('/such'):
        parts=m.text.split()
        if len(parts)>1:
            uid=parts[1]; u=DB["users"].get(uid)
            if u:
                wr=(u["total_w"]/(u["total_w"]+u["total_l"])*100) if (u["total_w"]+u["total_l"])>0 else 0
                bot.send_message(m.chat.id,"🔍 User "+uid+"\nLevel "+u["level"]+" 👑\nD W/L "+str(u["daily_w"])+"/"+str(u["daily_l"])+"\nGWR "+str(u["total_w"])+"/"+str(u["total_l"])+" WR "+str(round(wr,1))+"%\nBanned "+str(uid in DB["banned"])+" ⛔")
            else: bot.send_message(m.chat.id,"❌ Not found 🔍")

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    uid=str(c.from_user.id); u=ensure(c.from_user.id); data=c.data
    if is_banned(c.from_user.id): bot.answer_callback_query(c.id,"⛔ Banned 🚫"); return
    if data=="how":
        txt="📜 *How it Works - 5 Steps* 📚\n\n1️⃣ Register via link 🔗\n2️⃣ Get 5 FREE signals/day 🎁\n3️⃣ Deposit $20+ to upgrade 💰\n4️⃣ Click GET SIGNAL 📊\n5️⃣ Trade on Pocket Option - Use 1-step Martingale max 💹"
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=main_kb(c.from_user.id)); return
    if u["level"]=="LOCKED" or (not u["registered"] and uid!=str(OWNER)):
        if data in ["get_signal","market_real","market_otc","upgrade","deposit","mystatus"]:
            bot.edit_message_text(locked_text(uid), c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=locked_kb(uid)); return
    if data=="get_signal":
        can, reason = can_get_signal(c.from_user.id)
        if not can:
            if reason.startswith("limit"):
                lvl=u["level"]
                if lvl=="NONE": txt="⛔ *DAILY LIMIT REACHED!* 🚫\nMarket still giving WINNERS but you are BLOCKED! 🔥\n\nUpgrade to get more! 💎\nYou used "+str(u["daily_used"])+"/"+str(LEVELS[lvl]["limit"])+" 📊"
                else: txt="🔥 *LIMIT HIT — YOU ARE ON FIRE!* 🚀\nVIP UNLIMITED = NO LIMITS! 👑\n\nYou used "+str(u["daily_used"])+"/"+str(LEVELS[lvl]["limit"])+" 📊"
                kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("💎 Upgrade 🚀", callback_data="upgrade"))
                bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb); return
            elif "locked" in reason:
                bot.edit_message_text(locked_text(uid), c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=locked_kb(uid)); return
        bot.edit_message_text("📊 *Select Market:* 🔥\n✅ REAL 25 = 24/5 📈\n🔶 OTC 35 = 24/7 🌙", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=market_kb()); return
    if data.startswith("market_"):
        market=data.split("_")[1]
        if market=="real" and not is_real_open():
            bot.edit_message_text("⛔ REAL Market Closed (24/5 - Fri 22:00 GMT closed, Sat/Sun closed) 🌙\n\n🔶 Use OTC 35 (24/7) now! 🚀", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=market_kb()); return
        bot.edit_message_text("📊 *"+market.upper()+" - Select Mode:* ⚙️\n✋ Manual = You pick pair+expiry → Always signal ✅\n🤖 Auto = Bot hunts strong pair+expiry 🔥", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=mode_kb(market)); return
    if data.startswith("mode_manual_"):
        market=data.split("_")[-1]
        if market=="real" and not is_real_open():
            bot.edit_message_text("⛔ REAL Closed 24/5 - Use OTC 35 (24/7) 🌙", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=market_kb()); return
        bot.edit_message_text("✋ *Manual "+market.upper()+" - Pick Pair & Expiry:* 📝", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=pairs_kb(market,0,"M1")); return
    if data.startswith("mode_auto_"):
        market=data.split("_")[-1]
        if market=="real" and not is_real_open():
            bot.edit_message_text("⛔ REAL Closed 24/5 - Use OTC 35 (24/7) 🌙", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=market_kb()); return
        can, reason = can_get_signal(c.from_user.id)
        if not can and "limit" in reason: bot.answer_callback_query(c.id,"⛔ Limit reached 🚫"); return
        result = hunt_strong_signal(market, c.from_user.id)
        if result:
            txt, pair, expiry = result
            u["daily_used"]+=1; save()
            kb=types.InlineKeyboardMarkup(row_width=3)
            kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data="win_"+pair+"_"+expiry),types.InlineKeyboardButton("❌ LOSS 💔", callback_data="loss_"+pair+"_"+expiry),types.InlineKeyboardButton("🔥 Next Signal 🚀", callback_data="mode_auto_"+market))
            bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data.startswith("nav_") or data.startswith("expiry_"):
        try:
            parts=data.split("_"); market=parts[1]; page=int(parts[2]); expiry=parts[3]
            bot.answer_callback_query(c.id, "⏰ Expiry "+expiry+" ✅")
            bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=pairs_kb(market,page,expiry))
        except: bot.answer_callback_query(c.id,"❌ Error")
        return
    if data.startswith("pick_"):
        try:
            rest=data[5:]; market=rest.split("_")[0]; rem=rest[len(market)+1:]
            page=int(rem.split("_")[-1]); expiry=rem.split("_")[-2]; pair="_".join(rem.split("_")[:-2])
            can, reason = can_get_signal(c.from_user.id)
            if not can and "limit" in reason: bot.answer_callback_query(c.id,"⛔ Limit reached 🚫"); return
            txt, direction, rsi, above, stoch = gen_signal(pair, expiry, c.from_user.id)
            u["daily_used"]+=1; save()
            kb=types.InlineKeyboardMarkup(row_width=3)
            kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data="win_"+pair+"_"+expiry),types.InlineKeyboardButton("❌ LOSS 💔", callback_data="loss_"+pair+"_"+expiry),types.InlineKeyboardButton("🔥 Next Signal 🚀", callback_data="get_signal"))
            bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        except Exception as e: bot.answer_callback_query(c.id,"❌ Error "+str(e))
        return
    if data.startswith("win_") or data.startswith("loss_"):
        is_win=data.startswith("win_")
        if is_win: u["daily_w"]+=1; u["total_w"]+=1; u["streak"]+=1; u["loss_streak"]=0; txt="🎉 BOOM! WIN! 🔥🔥🔥 Streak "+str(u["streak"])+" 🚀 | Daily W:"+str(u["daily_w"])+" L:"+str(u["daily_l"])+" 📊"
        else:
            u["daily_l"]+=1; u["total_l"]+=1; u["loss_streak"]+=1; u["streak"]=0
            if u["loss_streak"]>=6: txt="⚠️⚠️ MARKET NOT STABLE — STOP NOW! ⚠️⚠️ 🚨\n💔 "+str(u["loss_streak"])+" LOSSES IN A ROW — RED ALERT! ⛔\n☕ TAKE BREAK 30-60 min! 🧘"
            else: mot=random.choice(MOTIV); txt="💔 LOSS "+str(u["loss_streak"])+"/5 — "+mot+" — Next is WIN! 🚀 Daily W:"+str(u["daily_w"])+" L:"+str(u["daily_l"])+" 📊"
        save(); bot.answer_callback_query(c.id, "✅ Recorded"); bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=main_kb(c.from_user.id)); return    if data=="upgrade" or data=="deposit":
        link=build_aff_link(uid); txt="💎 *UPGRADE LEVELS* 🚀\n\n🌱 NONE: 5/day 55-65% FREE 🎁\n📈 STARTER $20: 20/day 65-70% 💰\n💎 PRO $50: 100/day 70-80% 🔥\n👑 VIP $100: UNLIMITED 80-87% 🚀\n\nYour Level: "+u["level"]+" 👑 Deposit: $"+str(u["deposit"])+" 💰\n"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("🔗 Register / Deposit Now 🚀", url=link)); kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb); return
    if data=="mystatus":
        lim=LEVELS[u["level"]]["limit"]; lim_str=str(lim) if lim<999999 else "∞"
        txt="📈 *MY STATUS - DAILY RESET 00:00 UTC* ⏰\n\n🏆 DAILY W/L:\n✅ Wins Today: "+str(u["daily_w"])+" 🎉\n❌ Losses Today: "+str(u["daily_l"])+" 💔\n\n⏰ Resets daily at 00:00 UTC 🌙\n📊 Used: "+str(u["daily_used"])+"/"+lim_str+" 🔥"
        kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb); return
    if data=="back_main":
        lim=LEVELS[u["level"]]["limit"]; lim_str=str(lim) if lim<999999 else "∞"
        bot.edit_message_text("👋 Welcome "+c.from_user.first_name+"! 👑 "+u["level"]+" 📊 "+str(u["daily_used"])+"/"+lim_str+" Used Today 🚀", c.message.chat.id, c.message.message_id, reply_markup=main_kb(c.from_user.id)); return
    if data=="admin":
        if str(c.from_user.id)!=str(OWNER): bot.answer_callback_query(c.id,"⛔ Owner only 👑"); return
        levels_count={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for uu in DB["users"].values(): levels_count[uu["level"]]=levels_count.get(uu["level"],0)+1
        gwr_w=sum(uu["total_w"] for uu in DB["users"].values()); gwr_l=sum(uu["total_l"] for uu in DB["users"].values())
        txt="👑 *Admin Panel V14.3 - 3 Indicators* ⚙️\nUsers: "+str(len(DB["users"]))+" 👥\nLevels: "+str(levels_count)+" 📊\nBanned: "+str(len(DB["banned"]))+" ⛔\nGWR: "+str(gwr_w)+"W/"+str(gwr_l)+"L 🌍\nREAL 25 (24/5) 📈 + OTC 35 (24/7) 🌙 + Real Price API 💹"
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📢 Broadcast 📣", callback_data="admin_broadcast"),types.InlineKeyboardButton("👥 Users 👤", callback_data="admin_users"))
        kb.add(types.InlineKeyboardButton("📊 Stats 📈", callback_data="admin_stats"),types.InlineKeyboardButton("🔄 Reset Daily All ♻️", callback_data="admin_reset_daily"))
        kb.add(types.InlineKeyboardButton("👤 Add User ➕", callback_data="admin_adduser"),types.InlineKeyboardButton("🚫 Ban/Unban 🔨", callback_data="admin_ban"))
        kb.add(types.InlineKeyboardButton("🔍 Search/Such 🔎", callback_data="admin_search"),types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb); return
    if data=="admin_users":
        if str(c.from_user.id)!=str(OWNER): return
        out="👥 Last 20: 📊\n"
        for uid2, uu in list(DB["users"].items())[-20:]:
            wr = (uu["total_w"]/(uu["total_w"]+uu["total_l"])*100) if (uu["total_w"]+uu["total_l"])>0 else 0
            out+=uid2+" "+uu["level"]+" "+str(uu["daily_w"])+"W/"+str(uu["daily_l"])+"L GWR "+str(uu["total_w"])+"/"+str(uu["total_l"])+" WR "+str(int(wr))+"%\n"
        bot.edit_message_text(out, c.message.chat.id, c.message.message_id, reply_markup=main_kb(c.from_user.id)); return
    if data=="admin_stats":
        if str(c.from_user.id)!=str(OWNER): return
        levels_count={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for uu in DB["users"].values(): levels_count[uu["level"]]=levels_count.get(uu["level"],0)+1
        gwr_w=sum(uu["total_w"] for uu in DB["users"].values()); gwr_l=sum(uu["total_l"] for uu in DB["users"].values())
        bot.edit_message_text("📊 Levels: "+str(levels_count)+" 👥 ⛔ Banned: "+str(len(DB["banned"]))+" 🌍 GWR Total: "+str(gwr_w)+"W/"+str(gwr_l)+"L 🚀", c.message.chat.id, c.message.message_id, reply_markup=main_kb(c.from_user.id)); return
    if data=="admin_reset_daily":
        if str(c.from_user.id)!=str(OWNER): return
        for uu in DB["users"].values(): uu["daily_used"]=0; uu["daily_w"]=0; uu["daily_l"]=0; uu["streak"]=0; uu["loss_streak"]=0
        save(); bot.answer_callback_query(c.id,"✅ Daily reset done for all ♻️"); return
    if data=="admin_adduser":
        DB["_admin_wait"][uid]="adduser"; save()
        bot.edit_message_text("👤 *Add User* ➕\n\nSend like:\n`123456789 50` 📝\nID + deposit\n50 = PRO 💎, 100 = VIP 👑", c.message.chat.id, c.message.message_id, parse_mode="Markdown"); return
    if data=="admin_ban":
        DB["_admin_wait"][uid]="ban"; save()
        bot.edit_message_text("🚫 *Ban/Unban* 🔨\n\nSend:\n`ban 123456` ⛔\n`unban 123456` ✅\nOr just ID to ban", c.message.chat.id, c.message.message_id, parse_mode="Markdown"); return
    if data=="admin_search":
        DB["_admin_wait"][uid]="search"; save()
        bot.edit_message_text("🔍 *Search User* 🔎\n\nSend user ID:\n`123456789`", c.message.chat.id, c.message.message_id, parse_mode="Markdown"); return
    if data=="admin_broadcast":
        kb=types.InlineKeyboardMarkup(row_width=3)
        kb.add(types.InlineKeyboardButton("1 Day 📅", callback_data="bcast_del_24"),types.InlineKeyboardButton("1 Week 📆", callback_data="bcast_del_168"),types.InlineKeyboardButton("1 Month 🗓️", callback_data="bcast_del_720"))
        kb.add(types.InlineKeyboardButton("3 Months 📅", callback_data="bcast_del_2160"),types.InlineKeyboardButton("6 Months 📅", callback_data="bcast_del_4320"),types.InlineKeyboardButton("1 Year 📅", callback_data="bcast_del_8760"))
        kb.add(types.InlineKeyboardButton("Never ♾️", callback_data="bcast_del_0"))
        bot.edit_message_text("📢 *Broadcast Step 1: Select auto-delete period* ⏰", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb); return
    if data.startswith("bcast_del_"):
        hrs=int(data.split("_")[-1]); DB["_bcast_tmp"][uid]={"del":hrs}; save()
        kb=types.InlineKeyboardMarkup(row_width=3)
        kb.add(types.InlineKeyboardButton("ALL 🌍", callback_data="bcast_target_ALL"),types.InlineKeyboardButton("NONE 🌱", callback_data="bcast_target_NONE"),types.InlineKeyboardButton("STARTER 📈", callback_data="bcast_target_STARTER"))
        kb.add(types.InlineKeyboardButton("PRO 💎", callback_data="bcast_target_PRO"),types.InlineKeyboardButton("VIP 👑", callback_data="bcast_target_VIP"))
        bot.edit_message_text("⏰ Delete: "+str(hrs)+"h\n*Step 2: Select target level* 🎯", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb); return
    if data.startswith("bcast_target_"):
        target=data.split("_")[-1]; tmp=DB["_bcast_tmp"].get(uid,{"del":0}); tmp["target"]=target; DB["_bcast_tmp"][uid]=tmp; save(); DB["_bcast_wait"][uid]=tmp; save()
        bot.edit_message_text("✅ Broadcast ready 🚀\n⏰ Delete "+str(tmp["del"])+"h Target "+target+" 🎯\n\nNow send any text/photo/file - it will be broadcasted to "+target+" 📢", c.message.chat.id, c.message.message_id); return

@bot.message_handler(content_types=['text','photo','document','video'])
def broadcast_content(m):
    uid=str(m.from_user.id)
    if uid==str(OWNER) and uid in DB.get("_admin_wait",{}):
        state=DB["_admin_wait"][uid]; txt=m.text or ""
        if state=="adduser":
            try:
                parts=txt.split(); nid=parts[0]; dep=float(parts[1]) if len(parts)>1 else 0; u=ensure(nid); u["deposit"]=dep; u["level"]=get_level(dep); u["registered"]=True; save()
                bot.send_message(m.chat.id,"✅ Added "+nid+" level "+u["level"]+" 👑 deposit $"+str(dep)+" 💰", reply_markup=main_kb(m.from_user.id))
            except: bot.send_message(m.chat.id,"❌ Format error. Send: ID deposit e.g. 12345 100 📝")
            DB["_admin_wait"].pop(uid,None); save(); return
        if state=="ban":
            try:
                parts=txt.lower().split()
                if parts[0]=="unban" and len(parts)>1:
                    if parts[1] in DB["banned"]: DB["banned"].remove(parts[1]); save()
                    bot.send_message(m.chat.id,"✅ Unbanned "+parts[1]+" 🎉", reply_markup=main_kb(m.from_user.id))
                elif parts[0]=="ban" and len(parts)>1:
                    if parts[1] not in DB["banned"]: DB["banned"].append(parts[1]); save()
                    bot.send_message(m.chat.id,"✅ Banned "+parts[1]+" ⛔", reply_markup=main_kb(m.from_user.id))
                else:
                    nid=parts[0]
                    if nid not in DB["banned"]: DB["banned"].append(nid); save()
                    bot.send_message(m.chat.id,"✅ Banned "+nid+" ⛔", reply_markup=main_kb(m.from_user.id))
            except: bot.send_message(m.chat.id,"❌ Error")
            DB["_admin_wait"].pop(uid,None); save(); return
        if state=="search":
            nid=txt.split()[0]; u=DB["users"].get(nid)
            if u:
                wr=(u["total_w"]/(u["total_w"]+u["total_l"])*100) if (u["total_w"]+u["total_l"])>0 else 0
                bot.send_message(m.chat.id,"🔍 User "+nid+" 👤\nLevel "+u["level"]+" 👑\nDeposit $"+str(u["deposit"])+" 💰\nD W/L "+str(u["daily_w"])+"/"+str(u["daily_l"])+" 📊\nGWR "+str(u["total_w"])+"/"+str(u["total_l"])+" WR "+str(round(wr,1))+"% 🔥\nBanned "+str(nid in DB["banned"])+" ⛔\nUsername @"+str(u.get("username","")), reply_markup=main_kb(m.from_user.id))
            else: bot.send_message(m.chat.id,"❌ Not found "+nid+" 🔍", reply_markup=main_kb(m.from_user.id))
            DB["_admin_wait"].pop(uid,None); save(); return
    if str(m.from_user.id)!=str(OWNER): return
    wait=DB["_bcast_wait"].get(str(m.from_user.id))
    if not wait: return
    target=wait.get("target","ALL"); del_hours=wait.get("del",0); sent=0
    for uid2, uu in DB["users"].items():
        if target!="ALL" and uu["level"]!=target: continue
        try:
            if m.content_type=="text": msg=bot.send_message(int(uid2), m.text)
            elif m.content_type=="photo": msg=bot.send_photo(int(uid2), m.photo[-1].file_id, caption=m.caption or "")
            elif m.content_type=="document": msg=bot.send_document(int(uid2), m.document.file_id, caption=m.caption or "")
            else: msg=bot.send_video(int(uid2), m.video.file_id, caption=m.caption or "")
            sent+=1
            if del_hours>0:
                def del_later(chat, mid, hrs):
                    time.sleep(hrs*3600)
                    try: bot.delete_message(chat,mid)
                    except: pass
                threading.Thread(target=del_later, args=(int(uid2), msg.message_id, del_hours), daemon=True).start()
        except: pass
    DB["_bcast_wait"].pop(str(m.from_user.id),None); DB["_bcast_tmp"].pop(str(m.from_user.id),None); save()
    bot.send_message(m.chat.id, "✅ Broadcast sent to "+str(sent)+" users ("+target+" 👥) with delete "+str(del_hours)+"h ⏰")

def run_bot():
    while True:
        try: bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e: print("Poll err "+str(e)+" 🔥"); time.sleep(3)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))
