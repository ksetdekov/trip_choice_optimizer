import os
from aiogram import Bot, Dispatcher, types

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided in environment")

print(BOT_TOKEN)