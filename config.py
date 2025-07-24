# filepath: /Users/ksetdekov/Code/trip_choice_optimizer/config.py
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
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