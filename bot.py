import os, telebot
BOT_TOKEN = os.environ.get("BOT_TOKEN")
print("Token exists:", bool(BOT_TOKEN))
bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()
print("Webhook removed, starting polling...")

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✅ YES! I AM REPLYING! Owner 8188622130")

bot.infinity_polling()
