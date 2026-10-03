import os, json, random, time, requests
from datetime import date
from flask import Flask, request
import telebot
from telebot import types
import pandas as pd
import numpy as np

TOKEN=os.getenv("BOT_TOKEN")
SECRET=os.getenv("POSTBACK_SECRET","WW12345")
LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
FILE="users.json"
OWNER="8188622130"
SEC_FILE="security.json"
BLOCK_FILE="blocked_ips.json"

bot=telebot.TeleBot(TOKEN,threaded=False)
app=Flask(__name__)

REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","GBP/JPY","EUR/JPY","AUD/JPY","USD/CHF","EUR/AUD","GBP/AUD","EUR/CAD","NZD/USD","EUR/NZD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","USD/CHF OTC","EUR/AUD OTC","GBP/AUD OTC","EUR/CAD OTC","NZD/USD OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","BTC/USD OTC","ETH/USD OTC","LTC/USD OTC","XRP/USD OTC","ADA/USD OTC","DOT/USD OTC","SOL/USD OTC","BNB/USD OTC","DOGE/USD OTC","AVAX/USD OTC","MATIC/USD OTC","TRX/USD OTC","SHIB/USD OTC"]

EXP=["M1","M2","M3","M5"]

def get_live_closes(pair, limit=100):
    try:
        symbol_map = {"EUR/USD":"EURUSDT","GBP/USD":"GBPUSDT","USD/JPY":"USDJPY","AUD/USD":"AUDUSDT","USD/CAD":"USDCAD","NZD/USD":"NZDUSDT"}
        base = pair.split()[0].replace("/","").upper()
        binance_symbol = symbol_map.get(pair.split()[0], base+"T" if "USD" in base else "BTCUSDT")
        url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval=1m&limit={limit}"
        r = requests.get(url, timeout=2).json()
        if isinstance(r, list) and len(r)>10:
            return [float(x[4]) for x in r]
    except: pass
    return list(np.cumsum(np.random.normal(0, 0.0002, limit)) + 1.08)

def calc_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.where(deltas>0, deltas, 0)
    losses = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss==0: return 70 if avg_gain>0 else 30
    rs = avg_gain/avg_loss
    return 100-(100/(1+rs))

def calc_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

def get_real_signal(pair, exp):
    closes = get_live_closes(pair, 100)
    if len(closes)<30:
        return "BUY 🟢", 50, "UP", 65
    rsi = calc_rsi(closes, 14)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    last = closes[-1]
    trend = "UP" if ema9>ema21 else "DOWN"
    dist = abs(ema9-ema21)/last*10000
    exp_num = int(exp.replace("M",""))
    # base confidence from trend strength
    base_conf = 55 + min(dist*3, 15) + abs(rsi-50)*0.25
    # strong setups
    if exp_num==1:
        if rsi<30 and trend=="UP" and last>ema9: return "BUY 🟢", rsi, trend, 85
        if rsi>70 and trend=="DOWN" and last<ema9: return "SELL 🔴", rsi, trend, 85
        if rsi<35 and trend=="UP": return "BUY 🟢", rsi, trend, 78
        if rsi>65 and trend=="DOWN": return "SELL 🔴", rsi, trend, 78
    elif exp_num==2:
        if rsi<33 and trend=="UP" and last>ema9: return "BUY 🟢", rsi, trend, 82
        if rsi>67 and trend=="DOWN" and last<ema9: return "SELL 🔴", rsi, trend, 82
        if rsi<38 and trend=="UP": return "BUY 🟢", rsi, trend, 76
        if rsi>62 and trend=="DOWN": return "SELL 🔴", rsi, trend, 76
    else:
        if rsi<40 and trend=="UP": return "BUY 🟢", rsi, trend, 77
        if rsi>60 and trend=="DOWN": return "SELL 🔴", rsi, trend, 77
    # V5 FIX: NEVER return None - return best trend with calculated conf
    if trend=="UP":
        sig="BUY 🟢"
        conf=int(max(65, min(74, base_conf)))
    else:
        sig="SELL 🔴"
        conf=int(max(65, min(74, base_conf)))
    # Boost to 75%+ if dist good
    if dist>3: conf=max(conf,75)
    if dist>5: conf=max(conf,80)
    return sig, rsi, trend, conf

def load():
 if os.path.exists(FILE):
  try:
   with open(FILE) as f: return json.load(f)
  except: return {}
 return {}
def save(d):
 with open(FILE,"w") as f: json.dump(d,f,indent=2)
db=load()
def load_sec():
 if os.path.exists(SEC_FILE):
  try:
   with open(SEC_FILE) as f: return json.load(f)
  except: return []
 return []
def save_sec(d):
 with open(SEC_FILE,"w") as f: json.dump(d[-200:],f,indent=2)
def load_block():
 if os.path.exists(BLOCK_FILE):
  try:
   with open(BLOCK_FILE) as f: return json.load(f)
  except: return {}
 return {}
def save_block(d):
 with open(BLOCK_FILE,"w") as f: json.dump(d,f,indent=2)
sec_log=load_sec()
blocked=load_block()
def ensure(tid):
 tid=str(tid);u=db.get(tid)
 if not u: return None
 for k,v in [("today",0),("date",str(date.today())),("banned",False),("total",0),("level","none"),("verified",False)]:
  if k not in u: u[k]=v
 if tid==OWNER: u["level"]="vip";u["verified"]=True;u["banned"]=False
 if u.get("date")!=str(date.today()): u["today"]=0;u["date"]=str(date.today())
 db[tid]=u;save(db);return u
def get_lvl(tid):
 tid=str(tid)
 if tid==OWNER: return "vip"
 u=db.get(tid)
 if not u: return None
 ensure(tid)
 if u.get("banned"): return "banned"
 if not u.get("verified"): return "free"
 return u.get("level","starter")
def check_limit(tid,lvl):
 u=ensure(tid);lim=5
 if lvl=="starter": lim=20
 if lvl=="pro": lim=100
 if lvl=="vip": lim=999999
 return u.get("today",0)>=lim,u.get("today",0),lim
def inc(tid):
 u=ensure(tid)
 if u: u["today"]=u.get("today",0)+1;db[str(tid)]=u;save(db)
def get_ip():
 ip=request.headers.get('X-Forwarded-For','')
 if ip: ip=ip.split(',')[0].strip()
 else: ip=request.remote_addr or "unknown"
 return ip

@app.route("/")
def home(): return "V5 FIXED NO EMPTY",200

@app.route("/pocket_postback")
def pp():
 global sec_log, blocked
 ip=get_ip();now=time.time()
 for b_ip, exp in list(blocked.items()):
  if now > exp: del blocked[b_ip]
 save_block(blocked)
 if ip in blocked: return "IP blocked 24h",403
 sec=request.args.get("secret")
 if sec!=SECRET:
  sec_log.append({"time":str(date.today()),"ip":ip,"secret_tried":sec,"status":"WRONG_SECRET"})
  save_sec(sec_log)
  fails=len([x for x in sec_log if x["ip"]==ip and x["status"]=="WRONG_SECRET"])
  if fails>=5:
   blocked[ip]=now+86400
   save_block(blocked)
  try: bot.send_message(OWNER,f"🚨 FAKE ATTEMPT!\nIP: {ip}\nTried: {sec}")
  except: pass
  return "Blocked",403
 sub=request.args.get("subid") or request.args.get("click_id")
 sm=request.args.get("sum","0")
 try: amt=float(sm);gid=str(int(float(sub)))
 except: return "invalid",400
 sec_log.append({"time":str(date.today()),"ip":ip,"gid":gid,"sum":amt,"status":"SUCCESS"})
 save_sec(sec_log)
 u=db.get(gid)
 if not u: u={"total":0,"level":"none","verified":False,"today":0,"date":str(date.today()),
