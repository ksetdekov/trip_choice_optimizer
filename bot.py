import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F, Router
from aiogram import executor
from hands_table import HandsTable  # Assuming the refactored class is in hands_table.py

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided in environment")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
router = Router()

# Initialize a HandsTable instance (per bot or per user, as needed)
hands_table = HandsTable()

# Start command
@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Welcome! I am your HandsTable bot. Use /help to see available commands."
    )

# Help command
@router.message(Command("help"))
async def help(message: Message):
    await message.answer(
        "Here are the available commands:\n/start - Start the bot\n/help - Show this help message"
    )

# Add a new hand
@router.message(Command("add_hand"))
async def add_hand(message: Message):
    try:
        name = message.text.removeprefix("/add_hand ").strip()
        if not name:
            await message.answer("Please provide a name. Example: /add_hand coffee")
            return
        if name in hands_table.hands['name'].values:
            await message.answer(f"Hand '{name}' already exists.")
        else:
            hands_table.hands = hands_table.hands.append({'name': name, 'mu': 0, 'Te': 0, 'alpha': 0.5, 'beta': 0.5}, ignore_index=True)
            await message.answer(f"Hand '{name}' added successfully.")
    except Exception as e:
        await message.answer(f"Error: {e}")

# Update a hand's value
@router.message(Command("update_hand"))
async def update_hand(message: Message):
    try:
        args = message.text.removeprefix("/update_hand ").split()
        if len(args) != 2:
            await message.answer("Please provide a hand name and value. Example: /update_hand coffee 15")
            return
        name, value = args[0], float(args[1])
        if name not in hands_table.hands['name'].values:
            await message.answer(f"Hand '{name}' not found. Use /add_hand to add it first.")
        else:
            hands_table.update_hands(name, value)
            await message.answer(f"Hand '{name}' updated with value {value}.")
    except Exception as e:
        await message.answer(f"Error: {e}")

# Get grading/rankings
@router.message(Command("grade"))
async def grade(message: Message):
    try:
        ranked_df = hands_table.grade()
        response = ranked_df[['name', 'mu', 'Te', 'alpha', 'beta']].to_string(index=False)
        await message.answer(f"Rankings:\n<pre>{response}</pre>")
    except Exception as e:
        await message.answer(f"Error: {e}")

# Get history
@router.message(Command("history"))
async def history(message: Message):
    try:
        name = message.text.removeprefix("/history ").strip()
        if name:
            filtered_history = hands_table.history[hands_table.history['option'] == name]
            if filtered_history.empty:
                await message.answer(f"No history found for '{name}'.")
            else:
                response = filtered_history.to_string(index=False)
                await message.answer(f"History for '{name}':\n<pre>{response}</pre>")
        else:
            response = hands_table.history.to_string(index=False)
            await message.answer(f"Full History:\n<pre>{response}</pre>")
    except Exception as e:
        await message.answer(f"Error: {e}")

# Register the router with the dispatcher
dp.include_router(router)

# Start polling
if __name__ == "__main__":
    dp.run_polling(bot)
