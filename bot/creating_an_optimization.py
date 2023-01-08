import sys
import asyncio
import logging
from settings import BOT_TOKEN
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, F, Router, html
from typing import Any, Dict
list_of_options = []
optimization_direction = ["Минимизировать", "Максимизировать"]
risk_tolerance_options = ["Стандартная", "Низкая", "Высокая"]
# based on https://github.com/aiogram/aiogram/blob/dev-3.x/examples/finite_state_machine.py
risk_tolerance_mapping = {"Стандартная": 1, "Низкая": 1/3.37, "Высокая": 3.37}


form_router = Router()


class Form(StatesGroup):
    name = State()
    options = State()
    options_check = State()
    maximize = State()
    risk_tolerance = State()


@form_router.message(Command(commands=["new"]))
async def new_optimization(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        "Что будем оптимизировать?",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
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
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )


@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.options)
    await state.update_data(name=message.text)

    await message.reply(
        "Спасибо\nА какие варианты существуют?\nПеречислите через запятую.",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )


@form_router.message(Form.options)
async def process_options(message: Message, state: FSMContext) -> None:
    await state.update_data(options=message.text)
    print('options')
    if message.text is not None:
        print(message.text.split())
    data = await state.get_data()
    list_of_options = data.get("options", None)
    if list_of_options is not None:
        list_of_options = list_of_options.split(',')
        options_pretty = "\n".join(list_of_options)
    else:
        options_pretty = ''

    await message.answer(
        f"Спасибо, вы выбрали варианты :\n{options_pretty},\nСохранить и продолжить или ввести заново?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Continue"),
                    KeyboardButton(text="Repeat"),
                ]
            ],
            resize_keyboard=True,
        ),
    )
    data = await state.get_data()
    logging.info(data)
    await state.set_state(Form.options_check)
    # await show_summary(message=message, data=data)


@form_router.message(Form.options_check, F.text.casefold() == "continue")
async def process_dont_repeat_entry_options(message: Message, state: FSMContext) -> None:
    # data = await state.get_data()
    await message.answer(
        "Спасибо, а мы будем искать вариант, который минимизует целевое значение или максимизирует?\nНапример, найти тот день, где меньше людей в бассейне - минимизировать,\nа найти самую вкусную кофету - максимизировать",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Минимизировать"),
                    KeyboardButton(text="Максимизировать"),
                ]
            ],
            resize_keyboard=True,
        ))
    await state.set_state(Form.maximize)
    # await show_summary(message=message, data=data)


@form_router.message(Form.options_check, F.text.casefold() == "repeat")
async def process_repeat_entry_option(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.options)

    await message.reply(
        "Хорошо, введите варианты через замятую заново",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )


@form_router.message(Form.maximize)
async def process_options_minmax(message: Message, state: FSMContext) -> None:
    print(message.text)
    result_maximize = False
    if (message.text is not None):
        result_maximize = (message.text.lower() == 'Максимизировать')

    await state.update_data(maximize=result_maximize)
    await message.reply(
        f"Хорошо, спасибо, вы выбрали вариант {message.text}\nТеперь вопрос про склонность к риску.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Стандартная"),
                    KeyboardButton(text="Низкая"),
                    KeyboardButton(text="Высокая"),
                ]
            ],
            resize_keyboard=True,
        )
    )
    await state.set_state(Form.risk_tolerance)


@form_router.message(Form.risk_tolerance)
async def process_risk_tolerance_options(message: Message, state: FSMContext) -> None:
    risk_tolerance = 'стандартная'
    if message.text is not None:
        risk_tolerance = message.text.lower()
    await state.update_data(risk_tolerance=risk_tolerance)
    await message.reply(
        "Спасибо",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )

    data = await state.get_data()
    await show_summary(message=message, data=data)


async def show_summary(message: Message, data: Dict[str, Any]) -> None:
    name = data["name"]
    list_of_options = data.get("options")
    logging.info(list_of_options)
    text = f"оптимизируем: {html.quote(name)}, опции - {list_of_options}. Будет максимизация {data.get('maximize')}, Риск-толерантность {data.get('risk_tolerance')}"

    await message.answer(text=text, reply_markup=ReplyKeyboardRemove(remove_keyboard=True))


async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
