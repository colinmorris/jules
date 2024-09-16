import os

from dotenv import load_dotenv
import telebot

import jules as juleslib

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

jules = juleslib.Jules()

wakeup = jules.emit_wakeup_message()
bot.send_message(CHAT_ID, wakeup)
