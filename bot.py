import os, threading
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
LINKS = {
    "20": "https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801398&ac=wwpocket20&cid=984349",
    "50": "https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801400&ac=wwpocket50&cid=984350",
    "100": "https://u3.shortink.io/register?utm_campaign=868502&utm_source=affiliate&utm_medium=sr&a=jnLBWcb8IEyL7T&al=1801402&ac=wwpocket100&cid=984351"
}
USERS_DB = {}
app_flask = Flask(__name__)

@app_flask.route("/")
def home(): return "Bot is running"

@app_flask.route("/pocket_postback")
def pocket_postback():
    subid = request.args.get("subid")
    sum_depo = float(request.args.get("sum", 0) or 0)
    if subid:
        try:
            USERS_DB[int(subid)] = {"deposit": sum_depo}
        except: pass
    return "OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🟢 Starter $20 - 20 Signals/Day", callback_data="tier_20")],
        [InlineKeyboardButton("🔵 Pro $50 - 100 Signals/Day", callback_data="tier_50")],
        [InlineKeyboardButton("👑 VIP $100 - Unlimited", callback_data="tier_100")],
        [InlineKeyboardButton("✅ I Have Deposited", callback_data="check_depo")]
    ]
    await update.message.reply_text(f"Welcome!\nYour ID: {uid}\nChoose plan:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    if query.data.startswith("tier_"):
        tier = query.data.split("_")[1]
        final_link = f"{LINKS[tier]}&subid={uid}"
        keyboard = [[InlineKeyboardButton(f"Deposit ${tier} Now", url=final_link)], [InlineKeyboardButton("✅ I Have Deposited", callback_data="check_depo")]]
        await query.edit_message_text(f"Deposit ${tier} via link:\n{final_link}", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        data = USERS_DB.get(uid)
        if data:
            await query.edit_message_text(f"🎉 Deposit ${data['deposit']} Confirmed! Unlocked!")
        else:
            await query.edit_message_text(f"⏳ Not yet seen. ID: {uid}. Wait 2 mins.")

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

async def main_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    while True:
        await __import__("asyncio").sleep(3600)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    import asyncio
    asyncio.run(main_bot())
