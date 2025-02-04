import os
import logging  # new import
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from database_driver import DatabaseDriver

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)  # new logging configuration

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided in environment")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Simulated database to store optimizations
optimizations_db = DatabaseDriver()

class NewOptimization(StatesGroup):
    waiting_for_name = State()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        """Hello! I am your trip choice optimizer bot. 
I use Thompson Sampling algorithms for Mean-Variance Bandits to find the best options for your task, as described in the paper (https://arxiv.org/pdf/2002.00232.pdf). 
My optimization logic is implemented in the 'mvsampling' module. An example of this optimization is shown in this kaggle notebook  <a href="https://www.kaggle.com/code/ksetdekov/coffee-amount-optimization">ksetdekov/coffee-amount-optimization</a>. 
Send /help to see what I can do."""
    )

@dp.message(Command("new"))
async def new_optimization_command(message: types.Message, state: FSMContext):
    await message.answer("Please provide a name for the new optimization (e.g., 'commute time' or 'coffee cups'):")
    await state.set_state(NewOptimization.waiting_for_name)

@dp.message(NewOptimization.waiting_for_name)
async def process_new_optimization(message: types.Message, state: FSMContext):
    optimization_name = message.text.strip() # type: ignore
    optimizations_db.add_optimization(optimization_name, message.from_user.id) # type: ignore
    all_optimizations_for_this_user = optimizations_db.get_optimizations(message.from_user.id) # type: ignore
    await message.answer(f"Your new optimization '{optimization_name}' has been saved in the database. \n All your optimizations: {all_optimizations_for_this_user}")
    await state.clear()

@dp.message()  # new handler for unmatched messages
async def default_handler(message: types.Message):
    await message.answer("I didn't understand that command. Please use /start or /new.")

if __name__ == "__main__":
    dp.run_polling(bot)
