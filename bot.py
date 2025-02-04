import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided in environment")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        """Hello! I am your trip choice optimizer bot. 
I use Thompson Sampling algorithms for Mean-Variance Bandits to find the best options for your task, as described in the paper (https://arxiv.org/pdf/2002.00232.pdf). 
My optimization logic is implemented in the 'mvsampling' module. An example of this optimization is shown in this kaggle notebook  <a href="https://www.kaggle.com/code/ksetdekov/coffee-amount-optimization">ksetdekov/coffee-amount-optimization</a>. 
Send /help to see what I can do."""
    )

if __name__ == "__main__":
    dp.run_polling(bot)
