# import logging

import os
import telebot
from flask import Flask, request
# from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# from time_logger import *

if 'bot_token' in os.environ:
    TOKEN = os.environ['bot_token']
    print('getting token from env var')
else:
    print('getting token from file')
    from config_my import token
    TOKEN = token

PORT = int(os.environ.get('PORT', '8443'))

APP_URL = f'https://choice-optimizer.herokuapp.com/{TOKEN}'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo(message):
    bot.reply_to(message, message.text)


@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return '!', 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))