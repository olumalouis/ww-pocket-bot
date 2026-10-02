import os, threading, logging
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")

LINKS = {
    "20": "https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801398&ac=wwpocket20&cid=984349",
    "50": "https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801400&ac=wwpocket50&cid=984350",
    "100": "https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801402&ac=wwpocket100&cid=984351"
}
USERS_DB = {}

app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "WW Pocket Bot is LIVE!"

@app_flask.route("/pocket_postback")
def pocket_postback():
    subid = request.args.get("subid")
    sum_depo = float(request.args.get("sum", 0) or 0)
    if subid:
        try:
            USERS_DB[int(subid)] = {"deposit": sum_depo}
            print(f"DEPOSIT CONFIRMED: {subid} -> ${sum_depo}")
        except: pass
    return "OK", 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🟢 Starter $20 - 20 Signals/Day", callback_data="tier_20")],
        [InlineKeyboardButton("🔵 Pro $50 - 100 Signals/Day", callback_data="tier_50")],
        [InlineKeyboardButton("👑 VIP $100 - Unlimited", callback_data="tier_100")],
        [InlineKeyboardButton("✅ I Have Deposited", callback_data="check_depo")]
    ]
    await update.message.reply_text(f"Welcome to WW Pocket!\n\nYour ID: {uid}\nChoose plan to unlock signals:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    if query.data.startswith("tier_"):
        tier = query.data.split("_")[1]
        final_link = f"{LINKS[tier]}&subid={uid}"
        keyboard = [[InlineKeyboardButton(f"💳 Deposit ${tier} Now", url=final_link)], [InlineKeyboardButton("✅ I Have Deposited", callback_data="check_depo")]]
        await query.edit_message_text(f"Step 1: Deposit ${tier} via this tracked link:\n\n{final_link}\n\nStep 2: Click I Have Deposited after.", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        data = USERS_DB.get(uid)
        if data:
            await query.edit_message_text(f"🎉 DEPOSIT CONFIRMED!\nAmount: ${data['deposit']}\n\nYou are now UNLOCKED for signals! ✅")
        else:
            await query.edit_message_text(f"⏳ Not yet seen. Your ID: {uid}\n\nMake sure you used the link with subid. Wait 2 mins after deposit then click again.")

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Flask in background for postback
    threading.Thread(target=run_flask, daemon=True).start()
    print("Starting Telegram Bot polling...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
