from config import bot, dp

import handlers.optimizations

if __name__ == "__main__":
    dp.run_polling(bot)