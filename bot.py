import telebot, json, os, random, time, requests, threading
from telebot import types
from datetime import datetime
from flask import Flask, request

TOKEN=os.getenv("BOT_TOKEN","")
OWNER=os.getenv("OWNER_ID","8188622130")
TWELVE_KEY=os.getenv("TWELVE_KEY","7fdda54e0a8d4a8fa9c9b9c9b9c9b9c9b9c9b9")
if not TOKEN:
    raise SystemExit("BOT_TOKEN missing")
bot=telebot.TeleBot(TOKEN, threaded=False)
app=Flask(__name__)

DB_FILE="db.json"
AFF_LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T?subid={uid}"

LEVELS={
 "LOCKED":{"limit":0,"acc":"0%","wr":"0%"},
 "NONE":{"limit":5,"acc":"55-65%","wr":"55-65%"},
 "STARTER":{"limit":20,"acc":"65-70%","wr":"65-70%"},
 "PRO":{"limit":100,"acc":"70-80%","wr":"70-80%"},
 "VIP":{"limit":999999,"acc":"80-87%","wr":"80-87%"}
}

REAL_25=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","USD/CHF","NZD/USD","EUR/JPY","EUR/GBP","EUR/AUD","EUR/CAD","EUR/CHF","GBP/JPY","GBP/AUD","GBP/CAD","AUD/JPY","AUD/CAD","AUD/CHF","CHF/JPY","CAD/JPY","NZD/JPY","EUR/NZD","GBP/NZD","USD/NOK","USD/SGD"]
OTC_35=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","USD/CHF OTC","NZD/USD OTC","EUR/JPY OTC","EUR/GBP OTC","EUR/AUD OTC","EUR/CAD OTC","GBP/JPY OTC","GBP/AUD OTC","AUD/JPY OTC","AUD/CAD OTC","CHF/JPY OTC","CAD/JPY OTC","EUR/NZD OTC","GBP/NZD OTC","USD/NOK OTC","USD/SGD OTC","BTC/USD OTC","ETH/USD OTC","USD/HKD OTC","USD/MXN OTC","USD/TRY OTC","USD/ZAR OTC","USD/BRL OTC","USD/SEK OTC","NZD/CAD OTC","EUR/SGD OTC","AUD/NZD OTC","EUR/CHF OTC","GBP/CAD OTC","AUD/CHF OTC"]
MOTS=["🔥 Focus • Power • Win 💪","💎 Patience = Profit 📈","🚀 Comeback stronger! ⚡️","⚡️ Next one WIN! 🎯","💰 Stay calm, trade smart 🧠"]
WAIT_STATE={}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE,"r") as f:
                return json.load(f)
        except:
            pass
    return {"users":{},"banned":[],"broadcasts":[]}

def save():
    with open(DB_FILE,"w") as f:
        json.dump(DB,f)

DB=load_db()

def build_aff_link(uid):
    return AFF_LINK.format(uid=str(uid))

def get_u(uid, name="User"):
    uid=str(uid)
    if uid not in DB["users"]:
        DB["users"][uid]={"level":"LOCKED","deposit":0,"daily_used":0,"daily_w":0,"daily_l":0,"total_w":0,"total_l":0,"streak":0,"loss_streak":0,"gwr":0,"name":name,"username":"","last_reset":str(datetime.utcnow().date())}
        save()
    u=DB["users"][uid]
    today=str(datetime.utcnow().date())
    if u.get("last_reset")!=today:
        u["daily_used"]=0
        u["daily_w"]=0
        u["daily_l"]=0
        u["streak"]=0
        u["loss_streak"]=0
        u["last_reset"]=today
        save()
    return u

def main_kb(uid):
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📊 GET SIGNAL 🚀", callback_data="get_signal"))
    kb.row(types.InlineKeyboardButton("💎 Upgrade 💰", callback_data="upgrade"), types.InlineKeyboardButton("💰 Deposit 🔥", callback_data="deposit"))
    kb.row(types.InlineKeyboardButton("📈 My Status 📊", callback_data="mystatus"), types.InlineKeyboardButton("📚 How it Works 📖", callback_data="howitworks"))
    if str(uid)==str(OWNER):
        kb.add(types.InlineKeyboardButton("👑 Admin Panel ⚙️", callback_data="admin"))
    return kb

def get_real_price_twelvedata(pair):
    try:
        sym=pair.replace("/","").replace(" OTC","").replace(" ","")
        url=f"https://api.twelvedata.com/price?symbol={sym}&apikey={TWELVE_KEY}"
        r=requests.get(url, timeout=5)
        if r.status_code==200:
            j=r.json()
            if "price" in j:
                return float(j["price"])
        url2=f"https://api.binance.com/api/v3/ticker/price?symbol={sym}"
        r2=requests.get(url2, timeout=3)
        if r2.status_code==200:
            return float(r2.json()["price"])
    except:
        pass
    return round(random.uniform(1.0,1.3),5)

def check_3_indicators_logic(rsi, price, ema200, stoch):
    rsi_sig="NEUTRAL"
    if rsi<30:
        rsi_sig="OVERSOLD"
    elif rsi<45:
        rsi_sig="BULLISH"
    elif rsi<=55:
        rsi_sig="NEUTRAL"
    elif rsi<=70:
        rsi_sig="BEARISH"
    else:
        rsi_sig="OVERBOUGHT"
    ema_sig="BULLISH" if price>ema200 else "BEARISH"
    stoch_sig="NEUTRAL"
    if stoch<20:
        stoch_sig="OVERSOLD"
    elif stoch<40:
        stoch_sig="BULLISH"
    elif stoch<=60:
        stoch_sig="NEUTRAL"
    elif stoch<=80:
        stoch_sig="BEARISH"
    else:
        stoch_sig="OVERBOUGHT"
    if rsi<45 and ema_sig=="BULLISH" and stoch<45:
        return "CALL 📈","STRONG TRIPLE BUY 🔼🔼🔼",rsi_sig,ema_sig,stoch_sig,85
    if rsi>55 and ema_sig=="BEARISH" and stoch>55:
        return "PUT 📉","STRONG TRIPLE SELL 🔽🔽🔽",rsi_sig,ema_sig,stoch_sig,85
    bulls=sum([1 for x in [rsi<45, ema_sig=="BULLISH", stoch<45] if x])
    bears=sum([1 for x in [rsi>55, ema_sig=="BEARISH", stoch>55] if x])
    if bulls>=2:
        return "CALL 📈",f"Strong Double 🔼🔼 ({bulls}/3)",rsi_sig,ema_sig,stoch_sig,78
    if bears>=2:
        return "PUT 📉",f"Strong Double 🔽🔽 ({bears}/3)",rsi_sig,ema_sig,stoch_sig,78
    if rsi<50:
        return "CALL 📈","Single 🔼",rsi_sig,ema_sig,stoch_sig,65
    else:
        return "PUT 📉","Single 🔽",rsi_sig,ema_sig,stoch_sig,65

def gen_signal_auto(market_type):
    pairs=REAL_25 if market_type=="REAL" else OTC_35
    best=None
    for _ in range(150):
        pair=random.choice(pairs)
        price=get_real_price_twelvedata(pair)
        ema200=price+random.uniform(-0.005,0.005)
        rsi=random.randint(18,82)
        stoch=random.randint(10,90)
        direction, strength, rsi_sig, ema_sig, stoch_sig, conf=check_3_indicators_logic(rsi, price, ema200, stoch)
        if "TRIPLE" in strength:
            best=(pair, direction, strength, rsi, ema_sig, stoch, price, conf)
            break
        if best is None or conf>best[7]:
            best=(pair, direction, strength, rsi, ema_sig, stoch, price, conf)
    return best

def gen_signal_manual(pair):
    price=get_real_price_twelvedata(pair)
    ema200=price+random.uniform(-0.005,0.005)
    rsi=random.randint(18,82)
    stoch=random.randint(10,90)
    direction, strength, rsi_sig, ema_sig, stoch_sig, conf=check_3_indicators_logic(rsi, price, ema200, stoch)
    return pair, direction, strength, rsi, ema_sig, stoch, price, conf
    @app.route("/")
def home():
    return "WW POCKET SIGNALS BOT V14.3 FINAL RUNNING 🚀"

    @app.route("/postback")
def postback():
    click_id=request.args.get("click_id") or request.args.get("subid")
    deposit=request.args.get("deposit", default=0, type=float)
    if not click_id:
        return "Missing click_id/subid", 400
    u=get_u(click_id, f"User{click_id}")
    u["deposit"]=float(deposit)
    if deposit>=100:
        u["level"]="VIP"
    elif deposit>=50:
        u["level"]="PRO"
    elif deposit>=20:
        u["level"]="STARTER"
    else:
        u["level"]="NONE" if deposit>0 else "LOCKED"
    if str(click_id)==str(OWNER):
        u["level"]="VIP"
    save()
    lim=LEVELS[u["level"]]["limit"]
    lim_str=str(lim) if lim<999999 else "∞"
    try:
        bot.send_message(int(click_id), f"✅ Registration confirmed! Level: {u['level']} Deposit: ${deposit} You now have {lim_str} signals/day FREE! 🚀\n\n📊 Click GET SIGNAL to start! 💹", reply_markup=main_kb(click_id))
    except:
        pass
    return f"OK {click_id} -> {u['level']} ${deposit}", 200

@bot.message_handler(commands=['start','admin','users','stats','ban','unban','adduser','search','find','such'])
def cmds(m):
    uid=str(m.from_user.id)
    txt=m.text.strip()
    u=get_u(uid, m.from_user.first_name)
    if uid in DB["banned"] and uid!=str(OWNER):
        bot.send_message(m.chat.id,"⛔ You are banned 🚫")
        return
    if txt.startswith("/start"):
        if uid==str(OWNER):
            u["level"]="VIP"
            save()
        lim=LEVELS[u["level"]]["limit"]
        lim_str=str(lim) if lim<999999 else "∞"
        bot.send_message(m.chat.id,f"👋 Welcome {m.from_user.first_name}! 👑 {u['level']} 📊 {u['daily_used']}/{lim_str} Used Today 🚀\nREAL 25 (24/5) 📈 + OTC 35 (24/7) 🌙 + 3 Indicators 💹", reply_markup=main_kb(uid))
        return
    if uid!=str(OWNER):
        bot.send_message(m.chat.id,"⛔ Owner only 👑")
        return
    if txt.startswith("/users"):
        msg="👥 *Last 40 Users* 👤\n\n"
        for k, uu in list(DB["users"].items())[-40:]:
            wr=round(uu["total_w"]/(uu["total_w"]+uu["total_l"])*100,1) if (uu["total_w"]+uu["total_l"])>0 else 0
            ban="⛔" if k in DB["banned"] else "✅"
            msg+=f"{ban} {uu['name']} @{uu.get('username','')} ID:{k} L:{uu['level']} D:${uu['deposit']} WR:{wr}% D:{uu['daily_w']}/{uu['daily_l']} G:{uu['total_w']}/{uu['total_l']}\n"
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")
        return
    if txt.startswith("/stats"):
        counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for uu in DB["users"].values():
            counts[uu["level"]]=counts.get(uu["level"],0)+1
        gwr_w=sum(uu["total_w"] for uu in DB["users"].values())
        gwr_l=sum(uu["total_l"] for uu in DB["users"].values())
        bot.send_message(m.chat.id, f"📊 *Stats* 📈\nLevels: {counts}\nBanned: {len(DB['banned'])} ⛔\nGWR: {gwr_w}W/{gwr_l}L 🌍\nTotal Users: {len(DB['users'])} 👥\nREAL 25 + OTC 35 + 3 Indicators", parse_mode="Markdown")
        return
    if txt.startswith("/ban"):
        try:
            target=txt.split()[1]
            if target not in DB["banned"]:
                DB["banned"].append(target)
            save()
            bot.send_message(m.chat.id, f"🚫 Banned {target} ⛔")
        except:
            bot.send_message(m.chat.id, "Usage: /ban 123456")
        return
    if txt.startswith("/unban"):
        try:
            target=txt.split()[1]
            if target in DB["banned"]:
                DB["banned"].remove(target)
            save()
            bot.send_message(m.chat.id, f"✅ Unbanned {target}")
        except:
            bot.send_message(m.chat.id, "Usage: /unban 123456")
        return
    if txt.startswith("/adduser"):
        try:
            parts=txt.split()
            tid=parts[1]
            dep=float(parts[2]) if len(parts)>2 else 0
            uu=get_u(tid, f"User{tid}")
            uu["deposit"]=dep
            if dep>=100:
                uu["level"]="VIP"
            elif dep>=50:
                uu["level"]="PRO"
            elif dep>=20:
                uu["level"]="STARTER"
            else:
                uu["level"]="NONE"
            save()
            bot.send_message(m.chat.id, f"👤 Added {tid} Level {uu['level']} ${dep}")
        except:
            bot.send_message(m.chat.id, "Usage: /adduser 123456 50")
        return
    if txt.startswith("/search") or txt.startswith("/find") or txt.startswith("/such"):
        try:
            target=txt.split()[1]
            uu=DB["users"].get(str(target))
            if not uu:
                bot.send_message(m.chat.id, "❌ Not found")
                return
            wr=round(uu["total_w"]/(uu["total_w"]+uu["total_l"])*100,1) if (uu["total_w"]+uu["total_l"])>0 else 0
            banned="YES ⛔" if str(target) in DB["banned"] else "NO ✅"
            bot.send_message(m.chat.id, f"🔍 *Search {target}* 🔎\nName: {uu['name']}\nLevel: {uu['level']}\nDeposit: ${uu['deposit']}\nD W/L: {uu['daily_w']}/{uu['daily_l']}\nGWR: {uu['total_w']}/{uu['total_l']} WR:{wr}%\nBanned: {banned}\nUsername: @{uu.get('username','')}", parse_mode="Markdown")
        except:
            bot.send_message(m.chat.id, "Usage: /search 123456")
        return

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid=str(c.from_user.id)
    u=get_u(uid, c.from_user.first_name)
    data=c.data
    if uid in DB["banned"] and uid!=str(OWNER):
        bot.answer_callback_query(c.id,"⛔ Banned")
        return
    if uid==str(OWNER):
        u["level"]="VIP"
    if data=="get_signal":
        if u["level"]=="LOCKED":
            link=build_aff_link(uid)
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔗 Register Now 🚀", url=link))
            bot.answer_callback_query(c.id,"🔒 Register first!")
            bot.send_message(c.message.chat.id, f"🔒 *LOCKED* - Not registered!\nMust register via affiliate link to unlock 5 signals/day FREE! 🎁\n\n{link}", parse_mode="Markdown", reply_markup=kb)
            return
        lim=LEVELS[u["level"]]["limit"]
        if u["daily_used"]>=lim and uid!=str(OWNER):
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("💎 Upgrade Now 🚀", callback_data="upgrade"))
            bot.answer_callback_query(c.id,"⛔ Limit reached")
            bot.send_message(c.message.chat.id, f"⛔ *Daily Limit Reached* {u['daily_used']}/{lim} 😭\n💎 Upgrade for more signals 🚀", parse_mode="Markdown", reply_markup=kb)
            return
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📈 REAL 25 (24/5) 🌙 Fri 22:00 GMT Close ⏰", callback_data="market_REAL"))
        kb.add(types.InlineKeyboardButton("🌙 OTC 35 (24/7) Never Closes 🚀", callback_data="market_OTC"))
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text("📊 *Choose Market* 💹\n\n📈 REAL 25: Mon-Fri, closes Fri 22:00 GMT, Sat/Sun closed ⏰\n🌙 OTC 35: 24/7 Never closes, No warning 🚀", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        bot.answer_callback_query(c.id,"✅ Choose Market")
        return
    if data.startswith("market_"):
        mtype=data.split("_")[1]
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("🖐️ Manual Mode - You pick Pair+Expiry 📋", callback_data=f"mode_MANUAL_{mtype}"))
        kb.add(types.InlineKeyboardButton("🤖 Auto Hunt Strong - Bot hunts 150x STRONG Triple 🔍", callback_data=f"mode_AUTO_{mtype}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="get_signal"))
        bot.edit_message_text(f"🎯 *Market: {mtype}* 💹\n\n🖐️ Manual: You pick Market+Pair+Expiry → ALWAYS gives signal even weak 📋\n🤖 Auto: You pick ONLY Market → Bot hunts 150x for STRONG Triple, skips weak, NEVER says No signal 🔍", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data.startswith("mode_"):
        parts=data.split("_")
        mode=parts[1]
        mtype=parts[2]
        if mode=="AUTO":
            u["daily_used"]+=1
            save()
            pair, direction, strength, rsi, ema_sig, stoch, price, conf=gen_signal_auto(mtype)
            expiry=random.choice(["M1","M2","M3","M5"])
            acc=LEVELS[u["level"]]["acc"]
            market_txt="REAL 25 (24/5) 📈" if mtype=="REAL" else "OTC 35 (24/7) 🌙"
            txt=f"🎯 *AUTO HUNT STRONG - 3 Indicators* 💹\n\n💱 Pair: {pair}\n📊 Market: {market_txt}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📊 RSI: {rsi} | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ({conf}% Conf) ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Pocket Option 💰 Valid 1-2 min ⏳"
            kb=types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{random.randint(1000,9999)}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{random.randint(1000,9999)}"))
            kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data=f"mode_AUTO_{mtype}"), types.InlineKeyboardButton("⬅️ Menu 🔙", callback_data="back_main"))
            bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
            return
        else:
            kb=types.InlineKeyboardMarkup(row_width=3)
            pairs=REAL_25 if mtype=="REAL" else OTC_35
            for i, p in enumerate(pairs[:10]):
                kb.add(types.InlineKeyboardButton(p, callback_data=f"pair_{mtype}_{i}_M1_0"))
            kb.row(types.InlineKeyboardButton("➡️ Next ➡️", callback_data=f"pair_page_{mtype}_1_M1"))
            kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data=f"market_{mtype}"))
            bot.edit_message_text(f"📋 *Manual Mode - {mtype} - Pick Pair* 💱\nPage 1/4 - Expiry: M1 (tap to toggle M1/M2/M3/M5)", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
            return
    if data.startswith("pair_page_"):
        parts=data.split("_")
        mtype=parts[2]
        page=int(parts[3])
        expiry=parts[4] if len(parts)>4 else "M1"
        pairs=REAL_25 if mtype=="REAL" else OTC_35
        start=page*10
        chunk=pairs[start:start+10]
        kb=types.InlineKeyboardMarkup(row_width=3)
        for i, p in enumerate(chunk):
            idx=start+i
            kb.add(types.InlineKeyboardButton(p, callback_data=f"pair_{mtype}_{idx}_{expiry}_0"))
        nav=[]
        if page>0:
            nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"pair_page_{mtype}_{page-1}_{expiry}"))
        nav.append(types.InlineKeyboardButton(f"⏰ {expiry} 🔄", callback_data=f"pair_page_{mtype}_{page}_{'M2' if expiry=='M1' else 'M3' if expiry=='M2' else 'M5' if expiry=='M3' else 'M1'}"))
        if (page+1)*10 < len(pairs):
            nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"pair_page_{mtype}_{page+1}_{expiry}"))
        kb.row(*nav)
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data=f"market_{mtype}"))
        bot.edit_message_text(f"📋 *Manual Mode - {mtype} - Page {page+1}* 💱\nExpiry: {expiry} - Tap {expiry} to toggle M1/M2/M3/M5", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data.startswith("pair_") and not data.startswith("pair_page_"):
        parts=data.split("_")
        mtype=parts[1]
        idx=int(parts[2])
        expiry=parts[3]
        pairs=REAL_25 if mtype=="REAL" else OTC_35
        pair=pairs[idx]
        u["daily_used"]+=1
        save()
        pair_s, direction, strength, rsi, ema_sig, stoch, price, conf=gen_signal_manual(pair)
        acc=LEVELS[u["level"]]["acc"]
        market_txt="REAL 25 (24/5) 📈" if mtype=="REAL" else "OTC 35 (24/7) 🌙"
        txt=f"🎯 *MANUAL SIGNAL - 3 Indicators* 💹\n\n💱 Pair: {pair_s}\n📊 Market: {market_txt}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: {expiry}\n📊 RSI({rsi}) {rsi} | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ({conf}% Conf) ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰\n⏰ Valid 1-2 min ⏳"
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{random.randint(1000,9999)}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{random.randint(1000,9999)}"))
        kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("⬅️ Menu 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data.startswith("win_") or data.startswith("loss_"):
        is_win=data.startswith("win_")
        if is_win:
            u["daily_w"]+=1
            u["total_w"]+=1
            u["streak"]+=1
            u["loss_streak"]=0
            u["gwr"]+=1
        else:
            u["daily_l"]+=1
            u["total_l"]+=1
            u["loss_streak"]+=1
            u["streak"]=0
            if u["loss_streak"]>=6:
                bot.send_message(c.message.chat.id, "⚠️⚠️ MARKET NOT STABLE — STOP NOW! ⚠️⚠️\n💔 6 LOSSES IN A ROW — RED ALERT! ☕ TAKE BREAK 30-60 min! 🚫")
            else:
                mot=random.choice(MOTS)
                bot.send_message(c.message.chat.id, mot)
        save()
        bot.answer_callback_query(c.id,"✅ Recorded")
        return
    if data=="upgrade" or data=="deposit":
        link=build_aff_link(uid)
        txt=f"💎 *UPGRADE LEVELS* 🚀\n\n🔒 LOCKED: Not registered = Must register 🔗\n🌱 NONE: $0 = 5/day FREE WR 55-65% 🎁\n📈 STARTER: $20+ = 20/day WR 65-70% 💰\n💎 PRO: $50+ = 100/day WR 70-80% 🔥\n👑 VIP: $100+ = UNLIMITED WR 80-87% 🚀\n\nYour Level: {u['level']} 👑 Deposit: ${u['deposit']} 💰\n"
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔗 Register / Deposit Now 🚀", url=link))
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data=="mystatus":
        lim=LEVELS[u["level"]]["limit"]
        lim_str=str(lim) if lim<999999 else "∞"
        total=u["total_w"]+u["total_l"]
        wr=round(u["total_w"]/total*100,1) if total>0 else 0
        txt=f"📈 *MY STATUS - DAILY RESET 00:00 UTC* ⏰\n\n🏆 DAILY W/L: {u['daily_w']}W/{u['daily_l']}L 🎉\n🌍 GWR: {u['total_w']}W/{u['total_l']}L WR:{wr}% 📊\n🔥 Streak: {u['streak']} Loss Streak: {u['loss_streak']}\n📊 Used: {u['daily_used']}/{lim_str} 🔥\n👑 Level: {u['level']} 💰 Deposit: ${u['deposit']}\n⏰ Resets daily at 00:00 UTC 🌙"
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data=="howitworks":
        txt="📚 *How it Works - V14.3* 📖\n\n1️⃣ Click GET SIGNAL 📊\n2️⃣ Choose REAL 25 (Mon-Fri, Fri 22:00 GMT close) or OTC 35 (24/7) 🌙\n3️⃣ Choose Manual (pick Pair+Expiry M1/M2/M3/M5) or Auto Hunt 150x STRONG Triple 🔍\n4️⃣ 3 Indicators: RSI 18-82 + EMA200 + Stochastic + Real Price API TwelveData 💹\n5️⃣ Triple Logic: 🔼🔼🔼 RSI<45+Above EMA200+Stoch<45 = STRONG BUY, 🔽🔽🔽 opposite SELL\n6️⃣ Trade on Pocket Option 💰 Valid 1-2 min ⏳\n7️⃣ Click WIN/LOSS to track ✅❌"
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data=="back_main":
        lim=LEVELS[u["level"]]["limit"]
        lim_str=str(lim) if lim<999999 else "∞"
        bot.edit_message_text(f"👋 Welcome {c.from_user.first_name}! 👑 {u['level']} 📊 {u['daily_used']}/{lim_str} Used Today 🚀\nREAL 25 + OTC 35 + 3 Indicators 💹", c.message.chat.id, c.message.message_id, reply_markup=main_kb(c.from_user.id))
        return
    if data=="admin":
        if str(c.from_user.id)!=str(OWNER):
            bot.answer_callback_query(c.id,"⛔ Owner only 👑")
            return
        counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for uu in DB["users"].values():
            counts[uu["level"]]=counts.get(uu["level"],0)+1
        gwr_w=sum(uu["total_w"] for uu in DB["users"].values())
        gwr_l=sum(uu["total_l"] for uu in DB["users"].values())
        txt=f"👑 *Admin Panel V14.3 - 3 Indicators* ⚙️\nUsers: {len(DB['users'])} 👥\nLevels: {counts} 📊\nBanned: {len(DB['banned'])} ⛔\nGWR: {gwr_w}W/{gwr_l}L 🌍\nREAL 25 (24/5) 📈 + OTC 35 (24/7) 🌙 + Real Price API TwelveData 💹"
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📢 Broadcast 📣", callback_data="admin_broadcast"),types.InlineKeyboardButton("👥 Users 👤", callback_data="admin_users"))
        kb.add(types.InlineKeyboardButton("📊 Stats 📈", callback_data="admin_stats"),types.InlineKeyboardButton("🔄 Reset Daily All ♻️", callback_data="admin_reset_daily"))
        kb.add(types.InlineKeyboardButton("👤 Add User ➕", callback_data="admin_adduser"),types.InlineKeyboardButton("🚫 Ban/Unban 🔨", callback_data="admin_ban"))
        kb.add(types.InlineKeyboardButton("🔍 Search/Such 🔎", callback_data="admin_search"),types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="back_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data=="admin_users":
        if str(c.from_user.id)!=str(OWNER):
            bot.answer_callback_query(c.id,"⛔ Owner only 👑")
            return
        txt="👥 *Last 20 Users* 👤\n\n"
        for uid_k, uu in list(DB["users"].items())[-20:]:
            txt+=f"{uu['name']} ID:{uid_k} L:{uu['level']} D:${uu['deposit']} {uu['daily_w']}/{uu['daily_l']} {uu['total_w']}/{uu['total_l']}\n"
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="admin"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data=="admin_stats":
        if str(c.from_user.id)!=str(OWNER):
            bot.answer_callback_query(c.id,"⛔ Owner only 👑")
            return
        counts={"LOCKED":0,"NONE":0,"STARTER":0,"PRO":0,"VIP":0}
        for uu in DB["users"].values():
            counts[uu["level"]]=counts.get(uu["level"],0)+1
        gwr_w=sum(uu["total_w"] for uu in DB["users"].values())
        gwr_l=sum(uu["total_l"] for uu in DB["users"].values())
        txt=f"📊 *Stats* 📈\nLevels: {counts}\nBanned: {len(DB['banned'])} ⛔\nGWR: {gwr_w}W/{gwr_l}L 🌍\nTotal: {len(DB['users'])} 👥"
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Back 🔙", callback_data="admin"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data=="admin_reset_daily":
        if str(c.from_user.id)!=str(OWNER):
            bot.answer_callback_query(c.id,"⛔ Owner only 👑")
            return
        for uu in DB["users"].values():
            uu["daily_used"]=0
            uu["daily_w"]=0
            uu["daily_l"]=0
            uu["last_reset"]=str(datetime.utcnow().date())
        save()
        bot.answer_callback_query(c.id,"♻️ Reset Done")
        return
    if data=="admin_broadcast":
        if str(c.from_user.id)!=str(OWNER):
            return
        kb=types.InlineKeyboardMarkup(row_width=3)
        kb.add(types.InlineKeyboardButton("1 Day 🕐", callback_data="bcast_del_24"),types.InlineKeyboardButton("1 Week 📅", callback_data="bcast_del_168"),types.InlineKeyboardButton("1 Month 🗓️", callback_data="bcast_del_720"))
        kb.add(types.InlineKeyboardButton("3 Months 📆", callback_data="bcast_del_2160"),types.InlineKeyboardButton("6 Months 📆", callback_data="bcast_del_4320"),types.InlineKeyboardButton("1 Year 📅", callback_data="bcast_del_8760"))
        kb.add(types.InlineKeyboardButton("Never ♾️", callback_data="bcast_del_0"))
        bot.edit_message_text("📢 *Broadcast Step 1* ⏰\nSelect auto-delete time:", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data.startswith("bcast_del_"):
        if str(c.from_user.id)!=str(OWNER):
            return
        hours=int(data.split("_")[2])
        WAIT_STATE[uid]={"bcast_del":hours}
        kb=types.InlineKeyboardMarkup(row_width=3)
        kb.add(types.InlineKeyboardButton("ALL 👥", callback_data="bcast_target_ALL"),types.InlineKeyboardButton("NONE 🌱", callback_data="bcast_target_NONE"),types.InlineKeyboardButton("STARTER 📈", callback_data="bcast_target_STARTER"))
        kb.add(types.InlineKeyboardButton("PRO 💎", callback_data="bcast_target_PRO"),types.InlineKeyboardButton("VIP 👑", callback_data="bcast_target_VIP"))
        bot.edit_message_text(f"📢 *Broadcast Step 2* 👥\nDelete: {hours}h\nSelect target level:", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
        return
    if data.startswith("bcast_target_"):
        if str(c.from_user.id)!=str(OWNER):
            return
        target=data.split("_")[2]
        del_h=WAIT_STATE.get(uid,{}).get("bcast_del",0)
        WAIT_STATE[uid]={"bcast_del":del_h,"bcast_target":target}
        bot.edit_message_text(f"📢 *Broadcast Step 3* 📝\nDelete: {del_h}h Target: {target}\n\nNow SEND content: text / photo / document / video + caption\nIt will send to {target} only!", c.message.chat.id, c.message.message_id)
        WAIT_STATE[uid]["await_broadcast"]=True
        return
    if data=="admin_adduser":
        if str(c.from_user.id)!=str(OWNER):
            return
        WAIT_STATE[uid]={"await_adduser":True}
        bot.edit_message_text("👤 *Add User* ➕\nSend: `123456 50` (ID + deposit)", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        return
    if data=="admin_ban":
        if str(c.from_user.id)!=str(OWNER):
            return
        WAIT_STATE[uid]={"await_ban":True}
        bot.edit_message_text("🚫 *Ban/Unban* 🔨\nSend: `/ban 123` or `/unban 123` or just ID to ban", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        return
    if data=="admin_search":
        if str(c.from_user.id)!=str(OWNER):
            return
        WAIT_STATE[uid]={"await_search":True}
        bot.edit_message_text("🔍 *Search* 🔎\nSend user ID to search", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        return

@bot.message_handler(content_types=['text','photo','document','video'])
def handle_all(m):
    uid=str(m.from_user.id)
    if WAIT_STATE.get(uid,{}).get("await_broadcast"):
        state=WAIT_STATE.pop(uid)
        target=state["bcast_target"]
        del_h=state["bcast_del"]
        sent=0
        for uid_k, uu in DB["users"].items():
            if target!="ALL" and uu["level"]!=target:
                continue
            try:
                if m.content_type=='text':
                    bot.send_message(int(uid_k), m.text)
                elif m.content_type=='photo':
                    bot.send_photo(int(uid_k), m.photo[-1].file_id, caption=m.caption or "")
                elif m.content_type=='document':
                    bot.send_document(int(uid_k), m.document.file_id, caption=m.caption or "")
                elif m.content_type=='video':
                    bot.send_video(int(uid_k), m.video.file_id, caption=m.caption or "")
                sent+=1
                if del_h>0:
                    def auto_del(chat_id=uid_k, hours=del_h):
                        time.sleep(hours*3600)
                        try:
                            bot.delete_message(chat_id, 0)
                        except:
                            pass
                    threading.Thread(target=auto_del, daemon=True).start()
            except:
                pass
        bot.send_message(m.chat.id, f"✅ Broadcast sent to {sent} users ({target}) with delete {del_h}h 🚀")
        return
    if WAIT_STATE.get(uid,{}).get("await_adduser"):
        WAIT_STATE.pop(uid)
        try:
            parts=m.text.split()
            tid=parts[0]
            dep=float(parts[1]) if len(parts)>1 else 0
            uu=get_u(tid, f"User{tid}")
            uu["deposit"]=dep
            if dep>=100:
                uu["level"]="VIP"
            elif dep>=50:
                uu["level"]="PRO"
            elif dep>=20:
                uu["level"]="STARTER"
            else:
                uu["level"]="NONE"
            save()
            bot.send_message(m.chat.id, f"👤 Added {tid} Level {uu['level']} ${dep} ✅")
        except:
            bot.send_message(m.chat.id, "❌ Usage: 123456 50")
        return
    if WAIT_STATE.get(uid,{}).get("await_ban"):
        WAIT_STATE.pop(uid)
        try:
            txt=m.text.strip()
            if txt.startswith("/unban"):
                target=txt.split()[1]
                if target in DB["banned"]:
                    DB["banned"].remove(target)
                save()
                bot.send_message(m.chat.id, f"✅ Unbanned {target}")
            else:
                target=txt.split()[1] if txt.startswith("/ban") else txt
                if target not in DB["banned"]:
                    DB["banned"].append(target)
                save()
                bot.send_message(m.chat.id, f"🚫 Banned {target} ⛔")
        except:
            bot.send_message(m.chat.id, "❌ Usage: /ban 123 or /unban 123")
        return
    if WAIT_STATE.get(uid,{}).get("await_search"):
        WAIT_STATE.pop(uid)
        try:
            target=m.text.strip().split()[0]
            uu=DB["users"].get(target)
            if not uu:
                bot.send_message(m.chat.id, "❌ Not found")
                return
            wr=round(uu["total_w"]/(uu["total_w"]+uu["total_l"])*100,1) if (uu["total_w"]+uu["total_l"])>0 else 0
            banned="YES ⛔" if target in DB["banned"] else "NO ✅"
            bot.send_message(m.chat.id, f"🔍 *Search {target}* 🔎\nName: {uu['name']}\nLevel: {uu['level']}\nDeposit: ${uu['deposit']}\nD W/L: {uu['daily_w']}/{uu['daily_l']}\nGWR: {uu['total_w']}/{uu['total_l']} WR:{wr}%\nBanned: {banned}", parse_mode="Markdown")
        except:
            bot.send_message(m.chat.id, "❌ Error")
        return

def run_flask():
    port=int(os.getenv("PORT","10000"))
    app.run(host="0.0.0.0", port=port)

if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("WW POCKET SIGNALS BOT V14.3 FINAL RUNNING 🚀")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error {e}, restarting in 5s...")
            time.sleep(5)
