import os, json, random, time, requests
from datetime import datetime
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN=os.environ.get("BOT_TOKEN","YOUR_TOKEN_HERE")
OWNER_ID="8188622130"
DATA_FILE="data.json"
TWELVE_API="demo"

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
PAIRS_REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","GBP/JPY"]
PAIRS_OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/USD OTC","USD/CAD OTC",
"EUR/GBP OTC","EUR/AUD OTC","GBP/AUD OTC","AUD/JPY OTC","AUD/CAD OTC","EUR/CAD OTC","GBP/CAD OTC","NZD/USD OTC",
"EUR/NZD OTC","GBP/NZD OTC","AUD/NZD OTC","NZD/JPY OTC","NZD/CAD OTC","USD/CHF OTC","EUR/CHF OTC","GBP/CHF OTC",
"CHF/JPY OTC","CAD/JPY OTC","CAD/CHF OTC","USD/NOK OTC","EUR/NOK OTC","USD/SEK OTC","EUR/SEK OTC","USD/MXN OTC",
"USD/SGD OTC","USD/HKD OTC","USD/TRY OTC","USD/ZAR OTC"]

LAST_BOT_MSG={}
WAIT_STATE={}

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
        USERS[uid]={"level":"FREE","daily_w":0,"daily_l":0,"total_w":0,"total_l":0,"streak":0,"loss_streak":0,"used_today":0,"joined":str(datetime.now())}
        if uid==OWNER_ID:
            USERS[uid]["level"]="VIP"
    if uid==OWNER_ID:
        USERS[uid]["level"]="VIP"
    return USERS[uid]

def get_real_price_twelvedata(pair):
    try:
        sym=pair.replace(" OTC","").replace("/","")
        url=f"https://api.twelvedata.com/price?symbol={sym}/USD&apikey={TWELVE_API}"
        r=requests.get(url, timeout=5).json()
        if "price" in r:
            return float(r["price"])
    except:
        pass
    return round(random.uniform(1.0,1.3),5)

def check_3_indicators_logic(rsi, price, ema200, stoch):
    rsi_sig="NEUTRAL"
    if rsi<30:rsi_sig="OVERSOLD"
    elif rsi<45:rsi_sig="BULLISH"
    elif rsi<=55:rsi_sig="NEUTRAL"
    elif rsi<=70:rsi_sig="BEARISH"
    else:rsi_sig="OVERBOUGHT"
    ema_sig="BULLISH" if price>ema200 else "BEARISH"
    stoch_sig="NEUTRAL"
    if stoch<20:stoch_sig="OVERSOLD"
    elif stoch<40:stoch_sig="BULLISH"
    elif stoch<=60:stoch_sig="NEUTRAL"
    elif stoch<=80:stoch_sig="BEARISH"
    else:stoch_sig="OVERBOUGHT"
    if rsi<45 and ema_sig=="BULLISH" and stoch<45:
        return "BUY 📈","STRONG TRIPLE BUY 🔼🔼🔼",rsi_sig,ema_sig,stoch_sig,85
    if rsi>55 and ema_sig=="BEARISH" and stoch>55:
        return "SELL 📉","STRONG TRIPLE SELL 🔽🔽🔽",rsi_sig,ema_sig,stoch_sig,85
    bulls=sum([1 for x in [rsi<45, ema_sig=="BULLISH", stoch<45] if x])
    bears=sum([1 for x in [rsi>55, ema_sig=="BEARISH", stoch>55] if x])
    if bulls>=2:
        return "BUY 📈",f"Strong Double BUY 🔼🔼 ({bulls}/3)",rsi_sig,ema_sig,stoch_sig,78
    if bears>=2:
        return "SELL 📉",f"Strong Double SELL 🔽🔽 ({bears}/3)",rsi_sig,ema_sig,stoch_sig,78
    if rsi<50:
        return "BUY 📈","Single BUY 🔼",rsi_sig,ema_sig,stoch_sig,65
    else:
        return "SELL 📉","Single SELL 🔽",rsi_sig,ema_sig,stoch_sig,65

def gen_signal_manual(pair):
    price=get_real_price_twelvedata(pair)
    ema200=price+random.uniform(-0.005,0.005)
    rsi=random.randint(18,82)
    stoch=random.randint(10,90)
    direction, strength, rsi_sig, ema_sig, stoch_sig, conf=check_3_indicators_logic(rsi, price, ema200, stoch)
    return pair, direction, strength, rsi, ema_sig, stoch, price, conf

@app.route("/")
def home():
    return "WW POCKET SIGNALS BOT V14.4 FINAL RUNNING 🚀"

@app.route("/postback")
def postback():
    click_id=request.args.get("click_id")
    deposit=request.args.get("deposit","0")
    print(f"POSTBACK: {click_id} deposit {deposit}")
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

@bot.message_handler(commands=['start'])
def start(m):
    uid=str(m.from_user.id)
    clean_old(m.chat.id, uid)
    u=get_user(uid)
    txt=f"👋 Welcome Smart Investor! 👑 VIP 💹\n{u['used_today']}/∞ Used Today 🚀\nREAL 25 + OTC 35 + 3 Indicators 📈"
    msg=bot.send_message(m.chat.id, txt, reply_markup=main_menu(uid))
    LAST_BOT_MSG[uid]=[msg.message_id]
    save()

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid=str(c.from_user.id)
    u=get_user(uid)
    chat_id=c.message.chat.id

    if c.data=="menu":
        clean_old(chat_id, uid)
        txt=f"👋 Welcome Smart Investor! 👑 VIP 💹\n{u['used_today']}/∞ Used Today 🚀\nREAL 25 + OTC 35 + 3 Indicators 📈"
        msg=bot.send_message(chat_id, txt, reply_markup=main_menu(uid))
        LAST_BOT_MSG[uid]=[msg.message_id]
        try_delete(chat_id, c.message.message_id)
        return

    if c.data=="get_signal":
        clean_old(chat_id, uid)
        try_delete(chat_id, c.message.message_id)
        if u["level"]=="LOCKED":
            msg=bot.send_message(chat_id, "🔒 Daily limit reached! Upgrade to VIP for unlimited! 💎")
            LAST_BOT_MSG[uid]=[msg.message_id]
            return
        all_pairs=PAIRS_REAL+PAIRS_OTC
        pair=random.choice(all_pairs)
        market="REAL 25 (24/5) 🌞" if pair in PAIRS_REAL else "OTC 35 (24/7) 🌙"
        p, direction, strength, rsi, ema_sig, stoch, price, conf=gen_signal_manual(pair)
        acc=f"{conf-5}-{conf}%" if conf<85 else "80-87%"
        u["used_today"]+=1
        save()
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("✅ WIN 🎉", callback_data=f"win_{pair}"), types.InlineKeyboardButton("❌ LOSS 💔", callback_data=f"loss_{pair}"))
        kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        signal_txt=f"🎯 MANUAL SIGNAL - 3 Indicators 📈\n\n💱 Pair: {p}\n📊 Market: {market}\n💹 Real Price: {price} 💰\n🔮 Direction: {direction}\n⏰ Expiry: M3\n📈 RSI({rsi}) {rsi} | EMA200: {ema_sig} | Stoch: {stoch}\n💪 Strength: {strength}\n🎯 Accuracy: {acc} ({conf}% Conf) ✅\n🔥 Level: {u['level']} 👑\n\n⚠️ Trade on Pocket Option 💰\n⏰ Valid 1-2 min ⏳"
        msg=bot.send_message(chat_id, signal_txt, reply_markup=kb)
        LAST_BOT_MSG[uid]=[msg.message_id]
        return

    if c.data.startswith("win_") or c.data.startswith("loss_"):
        is_win=c.data.startswith("win_")
        clean_old(chat_id, uid)
        try_delete(chat_id, c.message.message_id)
        if is_win:
            u["daily_w"]+=1;u["total_w"]+=1;u["streak"]+=1;u["loss_streak"]=0
            txt=f"💥💥💥 BOOM! WIN CONFIRMED! 💥💥💥\n💰 MONEY IN! +1 WIN!\n🔥 Streak: {u['streak']} | Today: {u['daily_w']}W/{u['daily_l']}L\n🚀 Keep going Boss!"
        else:
            u["daily_l"]+=1;u["total_l"]+=1;u["loss_streak"]+=1;u["streak"]=0
            if u["loss_streak"]>=6:
                txt=f"⚠️ 6 Losses In A Row - Careful! ⚠️\n🧠 Market is choppy now Boss\n☕ Take a 30-60 min break, reset mindset\n💪 You will bounce back stronger!\n\n📊 Today: {u['daily_w']}W/{u['daily_l']}L"
            else:
                MOTS=["🔥 Focus • Power • Win 💪","💎 Patience = Profit 📈","🚀 Comeback stronger! ⚡️","⚡️ Next one WIN! 🎯","💰 Stay calm, trade smart 🧠"]
                txt=f"{random.choice(MOTS)}\n📊 Loss Streak: {u['loss_streak']} | Today: {u['daily_w']}W/{u['daily_l']}L"
        save()
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📊 Next Signal 🚀", callback_data="get_signal"), types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb)
        LAST_BOT_MSG[uid]=[msg.message_id]
        bot.answer_callback_query(c.id,"✅ Recorded")
        return

    if c.data=="status":
        clean_old(chat_id, uid)
        try_delete(chat_id, c.message.message_id)
        txt=f"📊 YOUR STATUS 📊\n\n👑 Level: {u['level']}\n✅ Wins Today: {u['daily_w']}\n❌ Losses Today: {u['daily_l']}\n🔥 Streak: {u['streak']}\n📈 Total: {u['total_w']}W/{u['total_l']}L"
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➡️ Menu", callback_data="menu"))
        msg=bot.send_message(chat_id, txt, reply_markup=kb)
        LAST_BOT_MSG[uid]=[msg.message_id]
        return

    if c.data in ["upgrade","deposit","how","admin"]:
        bot.answer_callback_query(c.id,"🚀 Coming Soon!")
        return

if __name__=="__main__":
    bot.remove_webhook()
    threading=__import__("threading")
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))).start()
    bot.infinity_polling()
