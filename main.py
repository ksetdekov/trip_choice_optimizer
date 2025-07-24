from config import bot, dp

import handlers.optimizations
import handlers.info_handler  

if __name__ == "__main__":
    dp.run_polling(bot)