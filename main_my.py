import telebot

import config_my
from parser_saver import *

bot = telebot.TeleBot(config_my.token)


@bot.message_handler(commands=["start"])
def hello(message):
    bot.send_message(message.chat.id, """Добрый день.\n
Я бот для поиска по странице https://wiki.openstreetmap.org/wiki/RU:Как_обозначить \n
Пока я умею только искать по заголовкам разделов и выводить их содержимое, но поиск будет работать как по частичному 
совпадению, так и по похожим словам\n
Введите название объекта:""")


@bot.message_handler(func=lambda message: message.text.lower().strip() != '/start')
def echo(message):
    bot.send_message(message.chat.id, 'Ищу...')
    result_answer = result_find(message.text)
    bot.send_message(message.chat.id, 'Найденный раздел - ' + result_answer[0])
    bot.send_message(message.chat.id, 'Совпадение с запросом : ' + str(result_answer[1]) + '%')
    bot.send_message(message.chat.id, result_answer[2])


if __name__ == '__main__':
    bot.infinity_polling()
