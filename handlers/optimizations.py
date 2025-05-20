import logging
from datetime import datetime

from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from tabulate import tabulate

import mvsampling.mvsampling as mv
from config import bot, dp, optimizations_db
from states import NewOptimization, NewOptionValue, NewVariant
from handlers.text_formatting import StringProcessor

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        """Hello! I am your trip choice optimizer bot. 
I use Thompson Sampling algorithms for Mean-Variance Bandits to find the best options for your task, as described in the paper (https://arxiv.org/pdf/2002.00232.pdf). 
My optimization logic is implemented in the 'mvsampling' module. An example of this optimization is shown in this <a href="https://www.kaggle.com/code/ksetdekov/coffee-amount-optimization">kaggle notebook</a>. 
Send /help to see what I can do."""
    )

@dp.message(Command("new"))
async def new_optimization_command(message: types.Message, state: FSMContext):
    await message.answer("Please provide a name for the new optimization (e.g., 'commute time' or 'coffee cups'):")
    await state.set_state(NewOptimization.waiting_for_name)

@dp.message(NewOptimization.waiting_for_name)
async def process_new_optimization(message: types.Message, state: FSMContext):
    optimization_name = message.text.strip()  # type: ignore
    # Ignore names starting with '/'
    if optimization_name.startswith("/"):
        await message.answer(
            "Invalid optimization name. Please provide a name that doesn't start with '/':\n"
            "e.g., 'commute time' or 'coffee cups'"
        )
        return
    # use text_formatting from StringProcessor to truncate the name
    processor = StringProcessor()
    optimization_name = processor.trunc64(optimization_name)

    # Check if the optimization name is already in use
    existing_optimizations = optimizations_db.get_optimizations(message.from_user.id)  # type: ignore
    if any(opt[0] == optimization_name for opt in existing_optimizations):
        await message.answer(
            "This optimization name already exists. Please provide a different name:"
        )
        return
    # Add the new optimization to the database
    optimizations_db.add_optimization(optimization_name, message.from_user.id)  # type: ignore
    all_optimizations_for_this_user = optimizations_db.get_optimizations(message.from_user.id)  # type: ignore
    await message.answer(
        f"Your new optimization '{optimization_name}' has been saved in the database.\n"
        f"All your optimizations: {all_optimizations_for_this_user}"
    )
    await state.clear()

@dp.message(Command("add_variant"))
async def add_variant_command(message: types.Message, state: FSMContext):
    # When retrieving optimizations from the database, ensure you get the id.
    optimizations = optimizations_db.get_optimizations(message.from_user.id)  # type: ignore # Each record: (optimization_name, change_datetime, optimization_id)

    if optimizations:
        keyboard = InlineKeyboardBuilder()
        for optimization in optimizations:
            # Assume your get_optimizations now returns (optimization_name, change_datetime, optimization_id)
            optimization_name = optimization[0]
            optimization_id = optimization[2]  # Get the id
            keyboard.button(
                text=optimization_name,
                callback_data=f"select_optimization:{optimization_id}"
            )
        keyboard.adjust(1) # one button per row
        await message.answer(
            "Please select the optimization to which you want to add a variant:",
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer("You don't have any optimizations yet. Please create one with /new.")

@dp.callback_query(lambda callback: callback.data and callback.data.startswith("select_optimization:"))
async def process_select_optimization(callback_query: CallbackQuery, state: FSMContext):
    # Extract the optimization id from the callback data
    optimization_id = callback_query.data.split(":", 1)[1] # type: ignore
    # Look up the full optimization name
    optimization_name = optimizations_db.get_optimization_name(optimization_id)  
    await state.update_data(optimization_id=optimization_id, optimization_name=optimization_name)
    
    if callback_query.message:
        await callback_query.message.edit_text(
            f"Selected optimization: {optimization_name}\nPlease provide the variant name or details:"
        )
    else:
        await callback_query.answer("Selected optimization, but no message found to edit.")
    await state.set_state(NewVariant.waiting_for_variant_name)
    await callback_query.answer()

@dp.message(NewVariant.waiting_for_optimization_name)
async def process_variant_optimization(message: types.Message, state: FSMContext):
    optimization_name = message.text.strip()  # type: ignore
    await state.update_data(optimization_name=optimization_name)
    await message.answer("Please provide the variant name or details:")
    await state.set_state(NewVariant.waiting_for_variant_name)

@dp.message(NewVariant.waiting_for_variant_name)
async def process_new_variant(message: types.Message, state: FSMContext):
    variant_name = message.text.strip()  # type: ignore
    data = await state.get_data()
    optimization_name = data.get("optimization_name")
    optimizations_db.add_variant(optimization_name, variant_name, message.from_user.id)  # type: ignore
    variants = optimizations_db.get_variants(optimization_name, message.from_user.id)  # type: ignore
    await message.answer(f"Variant '{variant_name}' added to optimization '{optimization_name}'.\nAll variants for this optimization: {variants}")
    await state.clear()

# remove optimization variants in the same way as optimizations
@dp.message(Command("delete_variant"))
async def delete_variant_command(message: types.Message, state: FSMContext):
    # Fetch all optimizations for the user
    optimizations = optimizations_db.get_optimizations(message.from_user.id)  # type: ignore
    keyboard = InlineKeyboardBuilder()
    found_any = False
    for optimization in optimizations:
        optimization_name = optimization[0]
        # Check if the optimization has any variants
        variants = optimizations_db.get_variants(optimization_name, message.from_user.id)  # type: ignore
        if variants:
            found_any = True
            keyboard.button(
                text=optimization_name,
                callback_data=f"delete_variant_opt:{optimization_name}"
            )
    if not found_any:
        await message.answer("No variants found for any optimization.")
    else:
        keyboard.adjust(1)  # one button per row
        await message.answer(
            "Please select the optimization from which you want to delete a variant:",
            reply_markup=keyboard.as_markup()
        )

@dp.callback_query(lambda callback: callback.data and callback.data.startswith("delete_variant_opt:"))
async def process_delete_variant_selection(callback_query: CallbackQuery, state: FSMContext):
    # Extract the selected optimization name.
    optimization_name = callback_query.data.split(":", 1)[1] # type: ignore
    # Build a keyboard with the list of variants for this optimization.
    variants = optimizations_db.get_variants(optimization_name, callback_query.from_user.id)  # type: ignore
    if not variants:
        await callback_query.answer("No variants found for the selected optimization.", show_alert=True)
        return
    keyboard = InlineKeyboardBuilder()
    for variant in variants:
        variant_name = variant[0]
        keyboard.button(
            text=variant_name,
            callback_data=f"delete_variant:{optimization_name}:{variant_name}"
        )
    keyboard.adjust(1)
    await callback_query.message.edit_text( # type: ignore
        f"Select the variant to delete from optimization '{optimization_name}':",
        reply_markup=keyboard.as_markup()
    )
    await callback_query.answer()

@dp.callback_query(lambda callback: callback.data and callback.data.startswith("delete_variant:"))
async def process_delete_variant(callback_query: CallbackQuery):
    # Expected callback data format: delete_variant:{optimization_name}:{variant_name}
    parts = callback_query.data.split(":", 2) # type: ignore
    if len(parts) < 3:
        await callback_query.answer("Invalid callback data.", show_alert=True)
        return
    optimization_name = parts[1]
    variant_name = parts[2]
    # Remove the selected variant from the database. Ensure that your DatabaseDriver has a remove_variant method.
    optimizations_db.remove_variant(optimization_name, variant_name, callback_query.from_user.id)  # type: ignore
    await callback_query.message.edit_text( # type: ignore
        f"Variant '{variant_name}' has been deleted from optimization '{optimization_name}'."
    )
    await callback_query.answer()

@dp.message(Command("delete_optimization"))
async def delete_optimization_command(message: types.Message):
    optimizations = optimizations_db.get_optimizations(message.from_user.id)  # type: ignore
    if optimizations:
        keyboard = InlineKeyboardBuilder()
        for optimization in optimizations:
            optimization_name = optimization[0]
            # Truncate the optimization name if it exceeds the callback data limit
            truncated_name = optimization_name[:50]  # Ensure callback data is within 64 characters
            keyboard.button(
                text=optimization_name,
                callback_data=f"delete_optimization:{truncated_name}"
            )
        keyboard.adjust(1)  # one button per row
        await message.answer(
            "Please select the optimization you want to delete:",
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer("You don't have any optimizations to delete.")

@dp.callback_query(lambda callback: callback.data and callback.data.startswith("delete_optimization:"))
async def process_delete_optimization(callback_query: CallbackQuery):
    # Extract the optimization name from the callback data
    optimization_name = callback_query.data.split(":", 1)[1]  # type: ignore
    # Remove the selected optimization
    optimizations_db.remove_optimization(optimization_name, callback_query.from_user.id)  # type: ignore
    if callback_query.message:
        await callback_query.message.edit_text(
            f"The optimization '{optimization_name}' has been deleted."
        )
    else:
        await bot.send_message(
            callback_query.from_user.id,
            f"The optimization '{optimization_name}' has been deleted."
        )
    await callback_query.answer()

@dp.message(Command("add_observation"))
async def add_observation_command(message: types.Message, state: FSMContext):
    # Get all optimizations for the user
    optimizations = optimizations_db.get_optimizations(message.from_user.id)  # type: ignore
    keyboard = InlineKeyboardBuilder()
    for optimization in optimizations:
        optimization_name = optimization[0]
        keyboard.button(
            text=optimization_name,
            callback_data=f"add_observation:{optimization_name}"
        )
    keyboard.adjust(1)  # one button per row
    
    await message.answer("Select the optimization for which to process observations:", reply_markup=keyboard.as_markup())


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("add_observation:"))
async def process_add_observation(callback_query: CallbackQuery, state: FSMContext):
    # Extract the selected optimization name
    optimization_name = callback_query.data.split(":", 1)[1]  # type: ignore
    user_id = callback_query.from_user.id
    # Retrieve all samples (observations) for this optimization
    samples = optimizations_db.get_all_samples_for_optimization(user_id, optimization_name)
    logging.debug("samples: %s", samples)
    # Build the events dictionary with datetime keys and tuple (optimization_name, option_value)
    events = {}
    for sample in samples:
        # sample is expected to be (optimization_name, option_value, change_datetime)
        _ , opt_name, option_value, change_dt = sample
        # Convert the change_dt to a datetime object if necessary
        if isinstance(change_dt, str):
            try:
                dt_obj = datetime.fromisoformat(change_dt)
            except Exception:
                continue
        else:
            dt_obj = change_dt
        events[dt_obj] = (opt_name, float(option_value))
    
    # get the options list from the database for variant initialization
    options_list = [variant[0] for variant in optimizations_db.get_variants(optimization_name, user_id)]
    # Create an instance of HandsTable; adjust the options list and minimize flag as required.
    # Currently hardcoded to maximize - here minimize=False
    logging.debug("options_list: %s", options_list)
    a = mv.HandsTable(options_list=options_list, minimize=False)
    logging.debug("events: %s", events)
    print(events)
    full_result = a.process_events(events)
    print(full_result)
    result = full_result[['name', 'mu', 'var95']]
    
    result_str = tabulate(result, headers='keys', showindex=False, tablefmt='pretty')  # type: ignore
    
    # Build an inline keyboard with up to 5 buttons, in the same order as in the result dataframe.
    keyboard = InlineKeyboardBuilder()
    for idx, row in result.head(5).iterrows():
        option = row['name']
        keyboard.button(
            text=str(option),
            callback_data=f"select_option:{optimization_name}:{option}"
        )
    keyboard.adjust(1)
    
    # Edit the message with the processed result and the inline keyboard
    if callback_query.message:
        await callback_query.message.edit_text(
            f"Processed observation result for '{optimization_name}':\n<pre>{result_str}</pre>\nBest option: {result.iloc[0]['name']}",
            reply_markup=keyboard.as_markup()
        )
    else:
        await bot.send_message(
            user_id,
            f"Processed observation result for '{optimization_name}':\n<pre>{result_str}</pre>\nBest option: {result.iloc[0]['name']}",
            reply_markup=keyboard.as_markup()
        )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("select_option:"))
async def process_select_option(callback_query: CallbackQuery, state: FSMContext):
    """
    When a user clicks an option button, prompt them to enter a value. 
    The callback data is expected to be in the form:
      select_option:{optimization_name}:{option}
    """
    # Extract the optimization name and option from callback data
    _, optimization_name, option = callback_query.data.split(":", 2) # type: ignore
    # Update state with the selected optimization and option.
    await state.update_data(selected_optimization=optimization_name, selected_option=option)
    prompt_text = f"Enter value for option '{option}' in optimization '{optimization_name}':"
    # Edit the message to prompt the user.
    if callback_query.message:
        await callback_query.message.edit_text(prompt_text)
    else:
        await bot.send_message(callback_query.from_user.id, prompt_text)
    await state.set_state(NewOptionValue.waiting_for_value)
    await callback_query.answer()

from aiogram.types import CallbackQuery, Message


@dp.message(NewOptionValue.waiting_for_value)
async def process_option_value(message: Message, state: FSMContext):
    """
    Process the user's input. Save the provided value for the selected option in the database.
    """
    data = await state.get_data()
    optimization_name = data.get("selected_optimization")
    option = data.get("selected_option")
    option_value = message.text.strip() # type: ignore
    # Write the option value to the database.
    optimizations_db.add_option(optimization_name=optimization_name, variant_name=option, option_value=option_value, user_id=message.from_user.id) # type: ignore
    await message.answer(f"Option '{option}' for optimization '{optimization_name}' saved with value '{option_value}'.")
    await state.clear()
