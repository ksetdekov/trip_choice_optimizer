import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from settings import BOT_TOKEN

dp = Dispatcher()


logger = logging.getLogger(__name__)



# async def start_handler(event: types.Message):
#     await event.answer(
#         f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",
#         parse_mode=types.ParseMode.HTML,
#     )

# async def echo_answer(event: types.Message):
#     await event.answer(event.text, parse_mode=types.ParseMode.HTML
#     )

# async def start_new_optimization(event: types.Message):
#     print([ event.from_user])
#     await event.answer(
#         f"Создал новую оптимизацию, {event.from_user.first_name}. Как её назвать?", parse_mode=types.ParseMode.HTML
#     )

# async def main():
#     bot = Bot(token=BOT_TOKEN)
#     try:
#         disp = Dispatcher(bot=bot)
#         disp.register_message_handler(start_handler, commands={"start", "restart"})
#         disp.register_message_handler(start_new_optimization, commands={"new"})

#         disp.register_message_handler(echo_answer, lambda msg: msg.text)
#         await disp.start_polling()
#     finally:
#         await bot.close()

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, stream=sys.stdout)
#     asyncio.run(main())


@dp.message(Command(commands=["start"]))
async def command_start_handler(message: Message) -> None:
    """
    This handler receive messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, <b>{message.from_user.full_name}!</b>")

@dp.message(Command(commands=["new"]))
async def new_handler(message: Message) -> None:
    """
    This handler receive messages with `/start` command
    """
    logger.info(message.from_user)
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Создал новую оптимизацию, {message.from_user.first_name}. Как её назвать?")


@dp.message()
async def echo_handler(message: types.Message) -> None:
    """
    Handler will forward received message back to the sender
    By default, message handler will handle all message types (like text, photo, sticker and etc.)
    """
    try:
        # Send copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


def main() -> None:
    # Initialize Bot instance with an default parse mode which will be passed to all API calls
    bot = Bot(BOT_TOKEN, parse_mode="HTML")
    # And the run events dispatching
    dp.run_polling(bot)


if __name__ == "__main__":
    main()