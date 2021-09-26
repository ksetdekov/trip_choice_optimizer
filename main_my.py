import logging
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# from time_logger import *

if 'bot_token' in os.environ:
    bot_token = os.environ.get('bot_token')
    print('getting token from env var')
else:
    print('getting token from file')
    from config_my import token

    bot_token = token

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("""Добрый день.\n
Я бот для поиска оптимального варианта в условиях неопределнности\n
Использую метод Томпсоновского сэмплирования для решения задачи многорукого бандита с нормальным распределением наград
и учетом неприятия риска\n
Можно использовать для поиска самого быстрого и стабильного вида транспорта на работу за минимум итерация.
введите через запятую варианты, которые будем перебирать:""")


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# """Start the bot."""
# Create the Updater and pass it your bot's token.
# Make sure to set use_context=True to use the new context based callbacks
# Post version 12 this will no longer be necessary
updater = Updater(bot_token)

# Get the dispatcher to register handlers
dp = updater.dispatcher

# on different commands - answer in Telegram
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help))

# on noncommand i.e message - echo the message on Telegram
dp.add_handler(MessageHandler(Filters.text, echo))

# log all errors
dp.add_error_handler(error)

# Start the Bot
PORT = int(os.environ.get("PORT", 3978))
updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=bot_token,
                      webhook_url='https://choice-optimizer.herokuapp.com/' + bot_token)

# Run the bot until you press Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
# add handlers
updater.idle()

