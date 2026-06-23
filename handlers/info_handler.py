from aiogram import types
from aiogram.filters import Command

from config import dp


@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "<b>Trip Choice Optimizer Bot</b>\n\n"
        "I help you choose what to try next, log the result, and learn from your history.\n\n"
        "<b>Commands</b>\n"
        "/start - greet the bot and get a recommendation or setup prompt\n"
        "/setup - create a new daily decision\n"
        "/recommend - get the next recommended option\n"
        "/log - save the result of an event\n"
        "/plots - show probability, distribution, or timeline plots\n"
        "/options - list options for the active decision\n"
        "/add_option - add an option to the active decision\n"
        "/remove_option - remove an option from the active decision\n"
        "/settings - view the active decision settings\n"
        "/cancel - leave the current flow\n\n"
        "Typical loop: ask /recommend, do the thing, then /log the measured value."
    )
    await message.answer(help_text)


@dp.message()
async def default_handler(message: types.Message):
    await message.answer(
        "I didn't understand that. Send /recommend for the next choice, "
        "/log to save a result, or /help for commands."
    )
