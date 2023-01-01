list_of_options = []
optimization_direction = ["Минимизировать", "Максимизировать"]
risk_tolerance_options = ["Стандартная", "Низкая", "Высокая"]
# based on https://github.com/aiogram/aiogram/blob/dev-3.x/examples/finite_state_machine.py
risk_tolerance_mapping = {"Стандартная":1, "Низкая":1/3.37, "Высокая":3.37}
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from settings import BOT_TOKEN

import logging

import asyncio
import logging
import sys
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

form_router = Router()

class Form(StatesGroup):
    name = State()
    options = State()
    direction = State()
    risk_tolerance = State()


@form_router.message(Command(commands=["new"]))
async def new_optimization(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        "Что будем оптимизировать?",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Command(commands=["cancel"]))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove(),
    )




@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.options)
    await message.answer(
        "Перечисли через запятую варианты ответов",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )
    data = await state.get_data()
    logging.info(data)
    await state.set_state(Form.options)
    # await show_summary(message=message, data=data)



@form_router.message(Form.options)
async def process_options(message: Message, state: FSMContext) -> None:
    data = await state.update_data(language=message.text)
    await state.clear()
    text = (
        "Thank for all! Python is in my hearth!\nSee you soon."
        if message.text.casefold() == "python"
        else "Thank for information!\nSee you soon."
    )
    await message.answer(text)
    await show_summary(message=message, data=data)
    

# @form_router.message(Form.like_bots, F.text.casefold() == "no")
# async def process_dont_like_write_bots(message: Message, state: FSMContext) -> None:
#     data = await state.get_data()
#     await state.clear()
#     await message.answer(
#         "Not bad not terrible.\nSee you soon.",
#         reply_markup=ReplyKeyboardRemove(),
#     )
#     await show_summary(message=message, data=data, positive=False)


# @form_router.message(Form.like_bots, F.text.casefold() == "yes")
# async def process_like_write_bots(message: Message, state: FSMContext) -> None:
#     await state.set_state(Form.language)

#     await message.reply(
#         "Cool! I'm too!\nWhat programming language did you use for it?",
#         reply_markup=ReplyKeyboardRemove(),
#     )


# @form_router.message(Form.like_bots)
# async def process_unknown_write_bots(message: Message, state: FSMContext) -> None:
#     await message.reply("I don't understand you :(")


# @form_router.message(Form.language)
# async def process_language(message: Message, state: FSMContext) -> None:
#     data = await state.update_data(language=message.text)
#     await state.clear()
#     text = (
#         "Thank for all! Python is in my hearth!\nSee you soon."
#         if message.text.casefold() == "python"
#         else "Thank for information!\nSee you soon."
#     )
#     await message.answer(text)
#     await show_summary(message=message, data=data)


async def show_summary(message: Message, data: Dict[str, Any], positive: bool = True) -> None:
    name = data["name"]
    list_of_options = data.get("language", "<something unexpected>")
    text = f"оптимизируем: {html.quote(name)}, "
    
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())


async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())