import os

from flask import Flask, request
from dotenv import load_dotenv
import telebot
import requests

app = Flask(__name__)

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LLM_API_KEY = os.getenv('LLM_API_KEY')
SERVER_URL = os.getenv('MY_SERVER_URL')

bot = telebot.TeleBot(BOT_TOKEN)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'OK', 200
    
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, message.text + '!!!')
    
if __name__ == '__main__':
    # Set up webhook
    bot.remove_webhook()
    bot.set_webhook(url=SERVER_URL + BOT_TOKEN)
    
    # Start Flask server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
