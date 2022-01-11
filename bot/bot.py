import logging
from aiogram.types import BotCommand
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
from bot.settings import (BOT_TOKEN, HEROKU_APP_NAME,
                          WEBHOOK_URL, WEBHOOK_PATH,
                          WEBAPP_HOST, WEBAPP_PORT, ADMIN_ID)

from bot.drinks import register_handlers_drinks
from bot.food import register_handlers_food
from bot.common import register_handlers_common

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/drinks", description="Заказать напитки"),
        BotCommand(command="/food", description="Заказать блюда"),
        BotCommand(command="/cancel", description="Отменить текущее действие")
    ]
    await bot.set_my_commands(commands)

    # Регистрация хэндлеров
    register_handlers_common(dp, ADMIN_ID)
    register_handlers_drinks(dp)
    register_handlers_food(dp)

    # Установка команд бота
    await set_commands(bot)

@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    """
    This handler will be called when user sends `/help` command
    """
    await message.reply("this is a help response")


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start`  command
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                         one_time_keyboard=True)
    buttons = ["Create new optimization", "Continue ...", "/help"]
    keyboard.add(*buttons)
    await message.answer("Hi!\nI'm choice_optimizer bot!\nSelect what you want to do?", reply_markup=keyboard)    


@dp.message_handler(commands="answer")
async def cmd_answer(message: types.Message):
    await message.answer("Это простой ответ")

@dp.message_handler()
async def echo(message: types.Message):
    logging.warning(f'Recieved a message from {message.from_user}')
    await message.answer(message.text)

async def on_startup(dp):
    logging.warning(
        'Starting connection. ')
    await bot.set_webhook(WEBHOOK_URL,drop_pending_updates=True)


async def on_shutdown(dp):
    logging.warning('Bye! Shutting down webhook connection')


def main():
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
