import os,json,random
from datetime import date,datetime
from flask import Flask,request
import telebot
from telebot import types

TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)
app=Flask(__name__)

LINK="https://u3.shortink.io/smart/jnLBWcb8IEyL7T"
FILE="users.json"
OWNER="8188622130"
SECRET=os.getenv("POSTBACK_SECRET","WW12345")

REAL=["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/JPY","EUR/GBP","NZD/USD","EUR/AUD","GBP/JPY","BTC/USD","ETH/USD"]
OTC=["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","EUR/JPY OTC","GBP/JPY OTC","BTC/USD OTC","ETH/USD OTC","EUR/GBP OTC","USD/BRL OTC","USD/INR OTC","USD/EGP OTC","USD/PKR OTC","USD/ARS OTC","USD/BDT OTC","USD/TRY OTC","USD/PHP OTC","NZD/USD OTC","EUR/AUD OTC","GBP/AUD OTC"]

last_bot_msg = {}

def clean_chat(chat_id, user_msg_id=None):
    try:
        if user_msg_id:
            bot.delete_message(chat_id, user_msg_id)
    except:
        pass
    try:
        if chat_id in last_bot_msg:
            bot.delete_message(chat_id, last_bot_msg[chat_id])
    except:
        pass

def send_clean(chat_id, text, reply_markup=None):
    try:
        msg = bot.send_message(chat_id, text, reply_markup=reply_markup)
        last_bot_msg[chat_id] = msg.message_id
        return msg
    except Exception as e:
        print("send_clean fail")

def load():
    if os.path.exists(FILE):
        try:
            with open(FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}

def save(d):
    with open(FILE,"w") as f:
        json.dump(d,f,indent=2)

db=load()

def ensure(tid):
    u=db.get(str(tid))
    if not u:
        return None
    if "today" not in u: u["today"]=0
    if "date" not in u: u["date"]=str(date.today())
    if "streak" not in u: u["streak"]=0
    if "banned" not in u: u["banned"]=False
    if "total" not in u: u["total"]=0
    if "level" not in u: u["level"]="none"
    if "verified" not in u: u["verified"]=False
    if "refs" not in u: u["refs"]=0
    if str(tid)==OWNER:
        u["level"]="vip"
        u["verified"]=True
        u["banned"]=False
    if u.get("date")!=str(date.today()):
        u["today"]=0
        u["date"]=str(date.today())
    db[str(tid)]=u
    save(db)
    return u

def get_lvl(tid):
    if str(tid)==OWNER:
        return "vip"
    u=db.get(str(tid))
    if not u:
        return None
    ensure(tid)
    if u.get("banned"):
        return "banned"
    if not u.get("verified"):
        return None
    return u.get("level","starter")

def check(tid,lvl):
    u=ensure(tid)
    if not u:
        return False,0,5
    lim=5
    if lvl=="starter": lim=20
    if lvl=="pro": lim=100
    if lvl=="vip": lim=999999
    used=u.get("today",0)
    return used>=lim,used,lim

def inc(tid):
    u=ensure(tid)
    if u:
        u["today"]=u.get("today",0)+1
        db[str(tid)]=u
        save(db)

def gen(pair,exp,lvl):
    cmin=75
    cmax=82
    if lvl=="pro":
        cmin=82
        cmax=89
    if lvl=="vip":
        cmin=89
        cmax=95
    act=random.choice(["BUY UP","SELL DOWN"])
    conf=random.randint(cmin,cmax)
    mt="OTC" if "OTC" in pair else "REAL"
    txt="SIGNAL "+lvl.upper()+"\nPair "+pair+"\nMarket "+mt+"\nExpiry "+exp+"\nAction "+act+"\nConf "+str(conf)+"%\nUTC "+datetime.utcnow().strftime('%H:%M')
    return txt,conf

@app.route("/")
def home():
    return "V3.4.2 Fixed"

@app.route("/"+TOKEN,methods=["POST"])
def wh():
    s=request.get_data().decode("utf-8")
    up=telebot.types.Update.de_json(s)
    bot.process_new_updates([up])
    return ""

@app.route("/pocket_postback")
def pp():
    sec=request.args.get("secret")
    if sec!=SECRET:
        return "Blocked",403
    sub=request.args.get("subid")
    if not sub:
        sub=request.args.get("click_id")
    sm=request.args.get("sum","0")
    try:
        amt=float(sm)
        gid=str(int(float(sub)))
    except:
        return "invalid",400
    u=db.get(gid)
    if not u:
        u={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False}
    tot=u.get("total",0)+amt
    lvl="none"
    if tot>=100: lvl="vip"
    elif tot>=50: lvl="pro"
    elif tot>=20: lvl="starter"
    u["total"]=tot
    u["level"]=lvl
    if tot>=20: u["verified"]=True
    else: u["verified"]=False
    db[gid]=u
    save(db)
    try:
        chat_id=int(gid)
        clean_chat(chat_id)
        if lvl!="none":
            k=types.InlineKeyboardMarkup()
            k.add(types.InlineKeyboardButton("START TRADING NOW",callback_data="go"))
            send_clean(chat_id, "DEPOSIT CONFIRMED $"+str(amt)+"\nUnlocked: "+lvl.upper()+"\nTotal: $"+str(tot), reply_markup=k)
        else:
            send_clean(chat_id, "Deposit $"+str(amt)+" added Total $"+str(tot))
    except Exception as e:
        print("notify fail")
    return "ok",200

def kb_start(tid):
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("START TRADING",callback_data="go"))
    k.add(types.InlineKeyboardButton("Deposit",callback_data="dep"),types.InlineKeyboardButton("My Status",callback_data="bal"))
    k.add(types.InlineKeyboardButton("Win Rate",callback_data="win"),types.InlineKeyboardButton("How to Use",callback_data="how"))
    k.add(types.InlineKeyboardButton("Referral",callback_data="ref"),types.InlineKeyboardButton("Support",callback_data="sup"))
    k.add(types.InlineKeyboardButton("Register",url=LINK+"?click_id="+tid))
    return k

def kb_admin():
    k=types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("Add VIP",callback_data="adm_addvip"),types.InlineKeyboardButton("Remove VIP",callback_data="adm_remvip"))
    k.add(types.InlineKeyboardButton("Ban/Unban",callback_data="adm_ban"),types.InlineKeyboardButton("Stats",callback_data="adm_stats"))
    k.add(types.InlineKeyboardButton("Broadcast",callback_data="adm_broad"),types.InlineKeyboardButton("Win Rate",callback_data="adm_win"))
    return k

@bot.message_handler(commands=["start"])
def st(m):
    tid=str(m.from_user.id)
    clean_chat(m.chat.id, m.message_id)
    args=m.text.split()
    inv=None
    if len(args)>1:
        inv=args[1].replace("ref_","")
    if tid not in db:
        db[tid]={"total":0,"level":"none","verified":False,"refs":0,"today":0,"date":str(date.today()),"streak":0,"banned":False,"inv":inv}
        if inv and inv in db and inv!=tid:
            db[inv]["refs"]=db[inv].get("refs",0)+1
        save(db)
    u=ensure(tid)
    if tid==OWNER:
        lv="VIP OWNER UNLIMITED"
        lim_txt="UNLIMITED"
    else:
        if not u.get("verified"):
            lv="FREE"
            lim_txt="5"
        else:
            lv=u.get("level","none").upper()
            lim_txt="20"
            if lv=="PRO": lim_txt="100"
            if lv=="VIP": lim_txt="UNLIMITED"
    used=u.get("today",0)
    msg="WELCOME V3.4\nFREE 0=5/day\n20=20/day\n50=100/day\n100=Unlimited\nLevel "+lv+"\nUsed "+str(used)+"/"+lim_txt+"\nReal 12 OTC 20\nID "+tid+"\n"+LINK+"?click_id="+tid
    if tid==OWNER:
        msg="OWNER VIP\n"+msg+"\n/admin for panel"
    send_clean(m.chat.id,msg,reply_markup=kb_start(tid))

@bot.message_handler(commands=["admin"])
def ad(m):
    tid=str(m.from_user.id)
    if tid!=OWNER:
        clean_chat(m.chat.id, m.message_id)
        send_clean(m.chat.id,"Owner only")
        return
    clean_chat(m.chat.id, m.message_id)
    tot=len(db)
    vip_c=0
    pro_c=0
    starter_c=0
    for x in db.values():
        if x.get("level")=="vip": vip_c+=1
        if x.get("level")=="pro": pro_c+=1
        if x.get("level")=="starter": starter_c+=1
    free_c=tot-vip_c-pro_c-starter_c
    dep=sum([x.get("total",0) for x in db.values()])
    today_c=0
    for x in db.values():
        if x.get("date")==str(date.today()):
            today_c+=x.get("today",0)
    msg="ADMIN PANEL V3.4\nUsers "+str(tot)+"\nVIP "+str(vip_c)+" PRO "+str(pro_c)+" STARTER "+str(starter_c)+" FREE "+str(free_c)+"\nDeposits $"+str
