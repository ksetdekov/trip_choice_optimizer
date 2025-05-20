from aiogram import types
from aiogram.filters import Command
from config import dp

@dp.message()  # Handler for unmatched messages
async def default_handler(message: types.Message):
    await message.answer(
        "I didn't understand that command. Select /help for an explaination\n"
        "Please use one of the following commands:\n"
        "- /start: Show the welcome message and available commands\n"
        "- /new: Create a new optimization\n"
        "- /add_variant: Add a variant to an optimization\n"
        "- /delete_variant: Delete a variant from an optimization\n"
        "- /delete_optimization: Delete an entire optimization\n"
        "- /add_observation: Add an observation for an optimization"
    )

@dp.message(Command("help"))  # Updated to use Command as a positional argument
async def help_command(message: types.Message):
    help_text = (
        "🤖 *Trip Choice Optimizer Bot Help*\n\n"
        "This bot uses Thompson Sampling algorithms for Mean-Variance Bandits to help you choose the best option from your list of commute options.\n\n"
        "*Commands:*\n"
        "• `/start` – Displays the welcome message and lists available commands.\n"
        "• `/new` – Create a new optimization by providing a name for your optimization scenario (e.g. 'Morning Commute').\n"
        "• `/add_variant` – Add a new variant to an existing optimization. You will be asked to select the optimization first, then provide the variant name.\n"
        "• `/delete_variant` – Remove an existing variant from an optimization.\n"
        "• `/delete_optimization` – Delete an optimization along with all its variants and observations.\n"
        "• `/add_observation` – Add an observation (or option) to an optimization, which the bot will process to suggest the best option.\n\n"
        "*How It Works:*\n"
        "1. *Optimizations*: Think of these as scenarios or decision problems, like choosing the best commute option.\n"
        "2. *Variants*: These are the available alternatives (e.g., different routes or transport options) within an optimization.\n"
        "3. *Observations*: For each variant, you can add sample data (like travel time or cost) which the bot uses in its sampling algorithm to rank the variants.\n\n"
        "The bot uses Thompson Sampling to balance exploration and exploitation so that over time it recommends the variant with the optimum balance of performance and uncertainty.\n\n"
        "If you have further questions, please consult the documentation or reach out to the support channel."
    )
    await message.answer(help_text, parse_mode="Markdown")
