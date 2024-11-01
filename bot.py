import logging
import os
import random
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided in environment")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Initialize SQLite database
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Create table to store user data
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT
)
''')

# Create table to store planned and actual interaction times
cursor.execute('''
CREATE TABLE IF NOT EXISTS plan_vs_act_interaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    planned_time TIMESTAMP,
    actual_time TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')
conn.commit()

# Greeting message for new users
@dp.message(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if result is None:
        # Save new user
        cursor.execute("INSERT INTO users (id, name) VALUES (?, ?)", (user_id, user_name))
        conn.commit()

        # Greeting for new users
        await message.reply("I'm a BeReal not. I try to estimate your active time during the day.")

# Send daily "Hi" and store the planned time
async def send_daily_hi(user_id: int):
    keyboard = InlineKeyboardMarkup(row_width=1)
    hi_button = InlineKeyboardButton("Hi", callback_data="hi")
    keyboard.add(hi_button)

    # Calculate the random next interaction time
    next_interaction = datetime.now() + timedelta(hours=random.randint(0, 23))

    # Record the planned interaction time in plan_vs_act_interaction table
    cursor.execute("INSERT INTO plan_vs_act_interaction (user_id, planned_time) VALUES (?, ?)",
                   (user_id, next_interaction))
    conn.commit()

    # Send the message at the planned interaction time
    await bot.send_message(chat_id=user_id, text="Please press 'Hi' to record your response!", reply_markup=keyboard)

# Callback handler for the "Hi" button
@dp.callback_query(lambda c: c.data == 'hi')
async def hi_button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    response_time = datetime.now()

    # Update the actual interaction time in the latest row for this user
    cursor.execute("""
        UPDATE plan_vs_act_interaction
        SET actual_time = ?
        WHERE user_id = ? AND actual_time IS NULL
        ORDER BY id DESC LIMIT 1
    """, (response_time, user_id))
    conn.commit()

    # Confirm the recorded response
    await bot.answer_callback_query(callback_query.id)
    if callback_query.message:
        await bot.edit_message_text(f"Hi! Response recorded at {response_time}.", chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id)

# Function to start sending "Hi" to all users at random times
async def daily_task():
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        await send_daily_hi(user_id)

# Run the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
