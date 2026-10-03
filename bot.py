import telebot, time, requests, pandas as pd, numpy as np, threading, os, json, re, random, sqlite3
from flask import Flask, request
from telebot import types
from datetime import datetime, timedelta

# === CONFIG ===
BOT_TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=7784787476
CHANNEL_ID="@WhiteWhalePocket"
POSTBACK_SECRET="WW12345"
POCKET_API="https://api-eu.po.market"
AFF_LINK="https://po-broker.in/l/Ql2gI0vD"
MIN_DEPOSIT=30
BOT_LINK="https://t.me/YourBotUsername"
DB_FILE="bot.db"
PAYOUT_FILE="payouts.json"
SETTINGS_FILE="settings.json"

bot=telebot.TeleBot(BOT_TOKEN, threaded=False)
app=Flask(__name__)

# === DB ===
conn=sqlite3.connect(DB_FILE, check_same_thread=False)
cur=conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (uid INTEGER PRIMARY KEY, dep REAL DEFAULT 0, ref INTEGER, joindate TEXT, username TEXT, tier TEXT DEFAULT 'STARTER', last_signal TEXT, warnings INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS refs (code TEXT PRIMARY KEY, owner INTEGER, uses INTEGER DEFAULT 0)")
conn.commit()

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE uid=?", (uid,))
    r=cur.fetchone()
    if not r:
        cur.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (uid,0,None,datetime.now().isoformat(), "", "STARTER", None, 0))
        conn.commit()
        return get_user(uid)
    return {"uid":r[0],"dep":r[1],"ref":r[2],"joindate":r[3],"username":r[4],"tier":r[5],"last_signal":r[6],"warnings":r[7]}

def update_dep(uid, amt):
    u=get_user(uid)
    new=max(u["dep"], amt)
    tier="VIP" if new>=50 else "STARTER"
    cur.execute("UPDATE users SET dep=?, tier=? WHERE uid=?", (new, tier, uid))
    conn.commit()

def load_json(f, d):
    if not os.path.exists(f): return d
    try:
        with open(f,"r") as fp: return json.load(fp)
    except: return d

def save_json(f, data):
    with open(f,"w") as fp: json.dump(fp, data)

payouts=load_json(PAYOUT_FILE, {})
settings=load_json(SETTINGS_FILE, {"auto_mode":False,"min_conf":65})

# === INDICATORS ===
def ema(s,p): return s.ewm(span=p, adjust=False).mean()
def rsi(s,p=14):
    d=s.diff(); g=d.where(d>0,0).rolling(p).mean(); l=(-d.where(d<0,0)).rolling(p).mean()
    rs=g/l; return 100-(100/(1+rs))
def supertrend(df, period=10, mult=3.0):
    hl2=(df['high']+df['low'])/2
    atr=(df['high']-df['low']).rolling(period).mean()
    up=hl2+mult*atr; dn=hl2-mult*atr
    st=[True]*len(df)
    for i in range(1,len(df)):
        if df['close'][i]<=dn[i-1]: st[i]=True
        elif df['close'][i]>=up[i-1]: st[i]=False
        else: st[i]=st[i-1]
    return st

def get_live_closes(market="EURUSD_otc", tf="1m", count=120):
    try:
        sym=market.replace("_otc","").replace("OTC","").upper()
        sym=sym.replace("100","").replace("200","").replace("300","").replace("500","").replace("1000","")
        url=f"https://api.twelvedata.com/time_series?symbol={sym}/USD&interval=1min&outputsize={count}&apikey=demo"
        r=requests.get(url, timeout=2).json()
        if "values" in r:
            return [float(x["close"]) for x in reversed(r["values"])]
    except: pass
    price=1.0850+random.uniform(-0.01,0.01)
    closes=[]
    for i in range(count):
        price+=random.uniform(-0.0005,0.0005)
        closes.append(price)
    return closes

def analyze(market, tf):
    tf_map={"5s":5,"15s":15,"30s":30,"1m":60,"2m":120,"3m":180,"5m":300}
    sec=tf_map.get(tf,60)
    closes=get_live_closes(market, tf, 120)
    if len(closes)<50: return None
    df=pd.DataFrame({"close":closes})
    df["high"]=df["close"]+0.0003; df["low"]=df["close"]-0.0003; df["open"]=df["close"].shift(1).fillna(df["close"])
    df["ema9"]=ema(df["close"],9); df["ema21"]=ema(df["close"],21); df["rsi"]=rsi(df["close"],14)
    st=supertrend(df); last=df.iloc[-1]; prev=df.iloc[-2]
    score=50; reasons=[]
    if last["ema9"]>last["ema21"]: score+=15; reasons.append("EMA Bullish")
    else: score-=15; reasons.append("EMA Bearish")
    if last["rsi"]<30: score+=15; reasons.append("RSI Oversold")
    elif last["rsi"]>70: score-=15; reasons.append("RSI Overbought")
    else:
        if prev["rsi"]<50 and last["rsi"]>50: score+=10; reasons.append("RSI Cross Up")
        if prev["rsi"]>50 and last["rsi"]<50: score-=10; reasons.append("RSI Cross Down")
    if st[-1]==True: score+=15; reasons.append("SuperTrend UP")
    else: score-=15; reasons.append("SuperTrend DOWN")
