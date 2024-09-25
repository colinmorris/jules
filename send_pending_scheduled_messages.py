import os

from dotenv import load_dotenv
import telebot

import jules as juleslib

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

jules = juleslib.Jules()

db = jules.scheduled_messages_db
pending = db.get_pending_messages()
for pend in pending:
    chat_msg = jules.emit_scheduled_message(pend)
    bot.send_message(CHAT_ID, chat_msg)
    db.mark_message_sent(pend['rowid'])
