import logging
import os

import telebot
from flask import Flask, request

import config_my

# from time_logger import *

bot = telebot.TeleBot(config_my.token)


@bot.message_handler(commands=["start"])
def hello(message):
    bot.send_message(message.chat.id, """Добрый день.\n
Я бот для поиска оптимального варианта в условиях неопределнности\n
Использую метод Томпсоновского сэмплирования для решения задачи многорукого бандита с нормальным распределением наград
и учетом неприятия риска\n
Можно использовать для поиска самого быстрого и стабильного вида транспорта на работу за минимум итерация.
введите через запятую варианты, которые будем перебирать:""")


@bot.message_handler(func=lambda message: message.text.lower().strip() != '/start')
def echo(message):
    bot.send_message(message.chat.id, 'ответ')


# Проверим, есть ли переменная окружения Хероку (как ее добавить смотрите ниже)
if "HEROKU" in list(os.environ.keys()):
    logger = telebot.logger
    telebot.logger.setLevel(logging.INFO)

    server = Flask(__name__)


    @server.route("/bot", methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200


    @server.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(
            url="https://choice-optimizer.herokuapp.com")  # этот url нужно заменить на url вашего Хероку приложения
        return "?", 200


    server.run(host="0.0.0.0", port=os.environ.get('PORT', 80))
else:
    # если переменной окружения HEROKU нету, значит это запуск с машины разработчика.
    # Удаляем вебхук на всякий случай, и запускаем с обычным поллингом.
    bot.remove_webhook()
    bot.polling(none_stop=True)
