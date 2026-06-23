import html
import os

from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import bot, dp, optimizations_db
from services.plots import (
    render_all_plots,
    render_distribution_plot,
    render_probability_plot,
    render_timeline_plot,
)
from services.recommendations import (
    format_ranking_table,
    get_active_or_only_optimization_id,
    get_recommendation,
)
from services.value_parsing import format_observation_value, parse_observation_value
from states import (
    LogObservation,
    OptionManagement,
    PlotFlow,
    RecommendationFlow,
    SetupOptimization,
)


def _optimization_keyboard(prefix, optimizations):
    keyboard = InlineKeyboardBuilder()
    for optimization_name, _, optimization_id in optimizations:
        keyboard.button(
            text=optimization_name,
            callback_data=f"{prefix}:{optimization_id}",
        )
    keyboard.adjust(1)
    return keyboard.as_markup()


def _variant_keyboard(prefix, variants, optimization_id):
    keyboard = InlineKeyboardBuilder()
    for variant_id, variant_name, _ in variants:
        keyboard.button(
            text=variant_name,
            callback_data=f"{prefix}:{optimization_id}:{variant_id}",
        )
    keyboard.adjust(1)
    return keyboard.as_markup()


def _recommendation_keyboard(optimization_id, variant_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Log this result",
        callback_data=f"log_result:{optimization_id}:{variant_id}",
    )
    keyboard.button(
        text="I chose another option",
        callback_data=f"log_other:{optimization_id}",
    )
    keyboard.button(
        text="Plots",
        callback_data=f"plots_for:{optimization_id}",
    )
    keyboard.button(
        text="Settings",
        callback_data=f"settings_for:{optimization_id}",
    )
    keyboard.adjust(1)
    return keyboard.as_markup()


def _setup_metric_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Time", callback_data="setup_metric:time")
    keyboard.button(text="Number", callback_data="setup_metric:number")
    keyboard.adjust(1)
    return keyboard.as_markup()


def _setup_objective_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Lower is better", callback_data="setup_objective:minimize")
    keyboard.button(text="Higher is better", callback_data="setup_objective:maximize")
    keyboard.adjust(1)
    return keyboard.as_markup()


def _setup_recency_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="360 days", callback_data="setup_recency:360")
    keyboard.button(text="180 days", callback_data="setup_recency:180")
    keyboard.button(text="90 days", callback_data="setup_recency:90")
    keyboard.button(text="Custom", callback_data="setup_recency:custom")
    keyboard.adjust(2)
    return keyboard.as_markup()


def _setup_rho_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Use default", callback_data="setup_rho:default")
    keyboard.button(text="Custom", callback_data="setup_rho:custom")
    keyboard.adjust(1)
    return keyboard.as_markup()


def _post_setup_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Recommend", callback_data="recommend_active")
    keyboard.button(text="Log old result", callback_data="log_active")
    keyboard.adjust(1)
    return keyboard.as_markup()


def _plot_type_keyboard(optimization_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Probability", callback_data=f"plot_type:{optimization_id}:probability")
    keyboard.button(text="Distribution", callback_data=f"plot_type:{optimization_id}:distribution")
    keyboard.button(text="Timeline", callback_data=f"plot_type:{optimization_id}:timeline")
    keyboard.button(text="All plots", callback_data=f"plot_type:{optimization_id}:all")
    keyboard.adjust(1)
    return keyboard.as_markup()


async def _ask_for_setup_name(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("What decision do you want to optimize?")
    await state.set_state(SetupOptimization.waiting_for_name)


async def _send_or_edit(callback_query: CallbackQuery, text, reply_markup=None):
    if callback_query.message:
        await callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await bot.send_message(callback_query.from_user.id, text, reply_markup=reply_markup)


async def _send_recommendation(chat, user_id, optimization_id, edit_callback=None):
    try:
        recommendation = get_recommendation(optimizations_db, user_id, optimization_id)
    except ValueError as exc:
        text = str(exc)
        if edit_callback is not None:
            await _send_or_edit(edit_callback, text)
        else:
            await chat.answer(text)
        return

    best_variant_id = recommendation.best_variant_id
    if best_variant_id is not None:
        optimizations_db.set_pending_recommendation(
            user_id,
            optimization_id,
            best_variant_id,
        )

    table = html.escape(format_ranking_table(recommendation))
    best_option = html.escape(str(recommendation.best_variant_name))
    optimization_name = html.escape(recommendation.optimization["optimization_name"])
    text = (
        f"For <b>{optimization_name}</b>, choose next:\n\n"
        f"<b>{best_option}</b>\n\n"
        f"Current ranking:\n<pre>{table}</pre>"
    )
    reply_markup = None
    if best_variant_id is not None:
        reply_markup = _recommendation_keyboard(optimization_id, best_variant_id)

    if edit_callback is not None:
        await _send_or_edit(edit_callback, text, reply_markup=reply_markup)
    else:
        await chat.answer(text, reply_markup=reply_markup)


async def _ask_optimization_for_recommendation(message: Message, state: FSMContext):
    optimizations = optimizations_db.get_optimizations(message.from_user.id)
    if not optimizations:
        await _ask_for_setup_name(message, state)
        return

    await message.answer(
        "Which decision should I recommend for?",
        reply_markup=_optimization_keyboard("recommend_opt", optimizations),
    )
    await state.set_state(RecommendationFlow.selecting_optimization)


async def _ask_optimization_for_log(message: Message, state: FSMContext):
    optimizations = optimizations_db.get_optimizations(message.from_user.id)
    if not optimizations:
        await _ask_for_setup_name(message, state)
        return

    await message.answer(
        "Which decision does this result belong to?",
        reply_markup=_optimization_keyboard("log_opt", optimizations),
    )
    await state.set_state(LogObservation.selecting_optimization)


async def _ask_variant_for_log(chat, optimization_id, state: FSMContext, user_id, edit_callback=None):
    variants = optimizations_db.get_variants_by_optimization_id(optimization_id)
    if not variants:
        text = "This decision has no options yet. Add options during /setup first."
        if edit_callback is not None:
            await _send_or_edit(edit_callback, text)
        else:
            await chat.answer(text)
        return

    optimization = optimizations_db.get_optimization_config(optimization_id, user_id=user_id)
    await state.update_data(log_optimization_id=optimization_id)
    await state.set_state(LogObservation.selecting_variant)
    text = f"Which option did you choose for '{optimization['optimization_name']}'?"
    reply_markup = _variant_keyboard("log_variant", variants, optimization_id)
    if edit_callback is not None:
        await _send_or_edit(edit_callback, text, reply_markup=reply_markup)
    else:
        await chat.answer(text, reply_markup=reply_markup)


async def _ask_log_value(
    chat,
    state,
    user_id,
    optimization_id,
    variant_id,
    edit_callback=None,
):
    optimization = optimizations_db.get_optimization_config(optimization_id, user_id=user_id)
    variant = optimizations_db.get_variant(variant_id, optimization_id=optimization_id)
    await state.update_data(
        log_optimization_id=optimization_id,
        log_variant_id=variant_id,
    )
    await state.set_state(LogObservation.waiting_for_value)

    if optimization["metric_type"] == "time":
        value_hint = "Send the result as 00:35:30 or as minutes."
    else:
        value_hint = "Send the result as a number."

    text = (
        f"Enter the observed value for '{variant['variant_name']}' "
        f"in '{optimization['optimization_name']}'.\n{value_hint}"
    )
    if edit_callback is not None:
        await _send_or_edit(edit_callback, text)
    else:
        await chat.answer(text)


def _format_options(optimization, variants):
    option_names = [variant_name for _, variant_name, _ in variants]
    escaped_name = html.escape(optimization["optimization_name"])
    if not option_names:
        return f"<b>{escaped_name}</b>\nNo options yet."

    options_text = "\n".join(f"- {html.escape(option)}" for option in option_names)
    return f"<b>{escaped_name}</b>\n{options_text}"


async def _finish_setup(callback_query, state):
    data = await state.get_data()
    optimization_id = optimizations_db.add_optimization(
        data["optimization_name"],
        callback_query.from_user.id,
        metric_type=data["metric_type"],
        objective=data["objective"],
        recency_days=data["recency_days"],
        rho=data["rho"],
    )
    optimizations_db.set_active_optimization(callback_query.from_user.id, optimization_id)
    await state.update_data(optimization_id=optimization_id, variant_count=0)
    await state.set_state(SetupOptimization.waiting_for_variants)
    await _send_or_edit(
        callback_query,
        "Add options one by one. Send /done when finished.",
    )


@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    optimizations = optimizations_db.get_optimizations(message.from_user.id)

    if not optimizations:
        await message.answer(
            "Hi. I can help you choose what to try next and learn from the result.\n"
            "Let's set up your first daily decision."
        )
        await _ask_for_setup_name(message, state)
        return

    if optimization_id is None:
        await _ask_optimization_for_recommendation(message, state)
        return

    await _send_recommendation(message, message.from_user.id, optimization_id)


@dp.message(Command("setup"))
@dp.message(Command("new"))
async def setup_command(message: Message, state: FSMContext):
    await _ask_for_setup_name(message, state)


@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Cancelled. Send /recommend when you want the next choice.")


@dp.message(SetupOptimization.waiting_for_name)
async def process_setup_name(message: Message, state: FSMContext):
    optimization_name = message.text.strip()
    if not optimization_name or optimization_name.startswith("/"):
        await message.answer("Send a plain name, for example Morning commute.")
        return

    existing = optimizations_db.get_optimizations(message.from_user.id)
    if any(row[0] == optimization_name for row in existing):
        await message.answer("You already have a decision with that name. Send a different name.")
        return

    await state.update_data(optimization_name=optimization_name)
    await message.answer(
        "What kind of result will you log?",
        reply_markup=_setup_metric_keyboard(),
    )
    await state.set_state(SetupOptimization.waiting_for_metric_type)


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("setup_metric:"))
async def process_setup_metric(callback_query: CallbackQuery, state: FSMContext):
    metric_type = callback_query.data.split(":", 1)[1]
    await state.update_data(metric_type=metric_type)
    await _send_or_edit(
        callback_query,
        "Do lower or higher values mean better?",
        reply_markup=_setup_objective_keyboard(),
    )
    await state.set_state(SetupOptimization.waiting_for_objective)
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("setup_objective:"))
async def process_setup_objective(callback_query: CallbackQuery, state: FSMContext):
    objective = callback_query.data.split(":", 1)[1]
    await state.update_data(objective=objective)
    await _send_or_edit(
        callback_query,
        "How many days of history should I use?",
        reply_markup=_setup_recency_keyboard(),
    )
    await state.set_state(SetupOptimization.waiting_for_recency)
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("setup_recency:"))
async def process_setup_recency_callback(callback_query: CallbackQuery, state: FSMContext):
    recency = callback_query.data.split(":", 1)[1]
    if recency == "custom":
        await state.update_data(waiting_for_custom_recency=True)
        await _send_or_edit(callback_query, "Send the number of days to keep in history.")
        await callback_query.answer()
        return

    await state.update_data(recency_days=int(recency), waiting_for_custom_recency=False)
    await _send_or_edit(
        callback_query,
        "Risk tolerance?",
        reply_markup=_setup_rho_keyboard(),
    )
    await state.set_state(SetupOptimization.waiting_for_rho)
    await callback_query.answer()


@dp.message(SetupOptimization.waiting_for_recency)
async def process_setup_recency_text(message: Message, state: FSMContext):
    try:
        recency_days = int(message.text.strip())
    except ValueError:
        await message.answer("Send a whole number of days, for example 360.")
        return

    if recency_days <= 0:
        await message.answer("History window must be at least 1 day.")
        return

    await state.update_data(recency_days=recency_days, waiting_for_custom_recency=False)
    await message.answer("Risk tolerance?", reply_markup=_setup_rho_keyboard())
    await state.set_state(SetupOptimization.waiting_for_rho)


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("setup_rho:"))
async def process_setup_rho_callback(callback_query: CallbackQuery, state: FSMContext):
    rho = callback_query.data.split(":", 1)[1]
    if rho == "custom":
        await state.update_data(waiting_for_custom_rho=True)
        await _send_or_edit(callback_query, "Send a numeric risk tolerance, for example 1.0.")
        await callback_query.answer()
        return

    await state.update_data(rho=1.0, waiting_for_custom_rho=False)
    await _finish_setup(callback_query, state)
    await callback_query.answer()


@dp.message(SetupOptimization.waiting_for_rho)
async def process_setup_rho_text(message: Message, state: FSMContext):
    try:
        rho = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Send a number, for example 1.0.")
        return

    if rho <= 0:
        await message.answer("Risk tolerance must be above zero.")
        return

    data = await state.get_data()
    optimization_id = optimizations_db.add_optimization(
        data["optimization_name"],
        message.from_user.id,
        metric_type=data["metric_type"],
        objective=data["objective"],
        recency_days=data["recency_days"],
        rho=rho,
    )
    optimizations_db.set_active_optimization(message.from_user.id, optimization_id)
    await state.update_data(optimization_id=optimization_id, variant_count=0)
    await message.answer("Add options one by one. Send /done when finished.")
    await state.set_state(SetupOptimization.waiting_for_variants)


@dp.message(SetupOptimization.waiting_for_variants, Command("done"))
async def finish_setup_variants(message: Message, state: FSMContext):
    data = await state.get_data()
    variant_count = data.get("variant_count", 0)
    if variant_count == 0:
        await message.answer("Add at least one option before finishing setup.")
        return

    await state.clear()
    await message.answer(
        "Setup complete. I can recommend what to try next, or you can log an old result.",
        reply_markup=_post_setup_keyboard(),
    )


@dp.message(SetupOptimization.waiting_for_variants)
async def process_setup_variant(message: Message, state: FSMContext):
    variant_name = message.text.strip()
    if not variant_name or variant_name.startswith("/"):
        await message.answer("Send an option name, or /done when finished.")
        return

    data = await state.get_data()
    optimization_id = data["optimization_id"]
    existing = optimizations_db.get_variants_by_optimization_id(optimization_id)
    if any(row[1] == variant_name for row in existing):
        await message.answer("That option is already added. Send another option or /done.")
        return

    optimizations_db.add_variant_by_id(optimization_id, variant_name)
    variant_count = data.get("variant_count", 0) + 1
    await state.update_data(variant_count=variant_count)
    await message.answer(f"Added {variant_name}. Send another option or /done.")


@dp.message(Command("recommend"))
async def recommend_command(message: Message, state: FSMContext):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    if optimization_id is None:
        await _ask_optimization_for_recommendation(message, state)
        return

    await _send_recommendation(message, message.from_user.id, optimization_id)


@dp.callback_query(lambda callback: callback.data == "recommend_active")
async def process_recommend_active(callback_query: CallbackQuery, state: FSMContext):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        callback_query.from_user.id,
    )
    if optimization_id is None:
        await _send_or_edit(callback_query, "I need a decision first. Send /setup.")
    else:
        await _send_recommendation(
            callback_query.message,
            callback_query.from_user.id,
            optimization_id,
            edit_callback=callback_query,
        )
    await state.clear()
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("recommend_opt:"))
async def process_recommend_optimization(callback_query: CallbackQuery, state: FSMContext):
    optimization_id = int(callback_query.data.split(":", 1)[1])
    optimizations_db.set_active_optimization(callback_query.from_user.id, optimization_id)
    await _send_recommendation(
        callback_query.message,
        callback_query.from_user.id,
        optimization_id,
        edit_callback=callback_query,
    )
    await state.clear()
    await callback_query.answer()


@dp.message(Command("log"))
async def log_command(message: Message, state: FSMContext):
    pending = optimizations_db.get_pending_recommendation(message.from_user.id)
    if pending is not None:
        await _ask_log_value(
            message,
            state,
            message.from_user.id,
            pending["optimization_id"],
            pending["variant_id"],
        )
        return

    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    if optimization_id is None:
        await _ask_optimization_for_log(message, state)
        return

    await _ask_variant_for_log(message, optimization_id, state, message.from_user.id)


@dp.callback_query(lambda callback: callback.data == "log_active")
async def process_log_active(callback_query: CallbackQuery, state: FSMContext):
    pending = optimizations_db.get_pending_recommendation(callback_query.from_user.id)
    if pending is not None:
        await _ask_log_value(
            callback_query.message,
            state,
            callback_query.from_user.id,
            pending["optimization_id"],
            pending["variant_id"],
            edit_callback=callback_query,
        )
    else:
        optimization_id = get_active_or_only_optimization_id(
            optimizations_db,
            callback_query.from_user.id,
        )
        if optimization_id is None:
            await _send_or_edit(callback_query, "I need a decision first. Send /setup.")
        else:
            await _ask_variant_for_log(
                callback_query.message,
                optimization_id,
                state,
                callback_query.from_user.id,
                edit_callback=callback_query,
            )
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("log_result:"))
async def process_log_recommended_result(callback_query: CallbackQuery, state: FSMContext):
    _, optimization_id, variant_id = callback_query.data.split(":", 2)
    await _ask_log_value(
        callback_query.message,
        state,
        callback_query.from_user.id,
        int(optimization_id),
        int(variant_id),
        edit_callback=callback_query,
    )
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("log_other:"))
async def process_log_other(callback_query: CallbackQuery, state: FSMContext):
    optimization_id = int(callback_query.data.split(":", 1)[1])
    await _ask_variant_for_log(
        callback_query.message,
        optimization_id,
        state,
        callback_query.from_user.id,
        edit_callback=callback_query,
    )
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("log_opt:"))
async def process_log_optimization(callback_query: CallbackQuery, state: FSMContext):
    optimization_id = int(callback_query.data.split(":", 1)[1])
    optimizations_db.set_active_optimization(callback_query.from_user.id, optimization_id)
    await _ask_variant_for_log(
        callback_query.message,
        optimization_id,
        state,
        callback_query.from_user.id,
        edit_callback=callback_query,
    )
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("log_variant:"))
async def process_log_variant(callback_query: CallbackQuery, state: FSMContext):
    _, optimization_id, variant_id = callback_query.data.split(":", 2)
    await _ask_log_value(
        callback_query.message,
        state,
        callback_query.from_user.id,
        int(optimization_id),
        int(variant_id),
        edit_callback=callback_query,
    )
    await callback_query.answer()


@dp.message(LogObservation.waiting_for_value)
async def process_log_value(message: Message, state: FSMContext):
    data = await state.get_data()
    optimization_id = data["log_optimization_id"]
    variant_id = data["log_variant_id"]
    optimization = optimizations_db.get_optimization_config(
        optimization_id,
        user_id=message.from_user.id,
    )
    variant = optimizations_db.get_variant(variant_id, optimization_id=optimization_id)

    try:
        parsed_value = parse_observation_value(message.text, optimization["metric_type"])
    except ValueError as exc:
        await message.answer(str(exc))
        return

    optimizations_db.add_sample_by_ids(optimization_id, variant_id, parsed_value)
    optimizations_db.clear_pending_recommendation(message.from_user.id)
    await state.clear()

    formatted_value = format_observation_value(parsed_value, optimization["metric_type"])
    await message.answer(
        f"Saved: {variant['variant_name']} = {formatted_value}."
    )
    await _send_recommendation(message, message.from_user.id, optimization_id)


@dp.message(Command("plots"))
async def plots_command(message: Message, state: FSMContext):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    if optimization_id is None:
        optimizations = optimizations_db.get_optimizations(message.from_user.id)
        if not optimizations:
            await _ask_for_setup_name(message, state)
            return
        await message.answer(
            "Which decision should I plot?",
            reply_markup=_optimization_keyboard("plot_opt", optimizations),
        )
        await state.set_state(PlotFlow.selecting_optimization)
        return

    await message.answer(
        "Which plot do you want?",
        reply_markup=_plot_type_keyboard(optimization_id),
    )
    await state.set_state(PlotFlow.selecting_plot_type)


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("plots_for:"))
async def process_plots_for(callback_query: CallbackQuery, state: FSMContext):
    optimization_id = int(callback_query.data.split(":", 1)[1])
    await _send_or_edit(
        callback_query,
        "Which plot do you want?",
        reply_markup=_plot_type_keyboard(optimization_id),
    )
    await state.set_state(PlotFlow.selecting_plot_type)
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("plot_opt:"))
async def process_plot_optimization(callback_query: CallbackQuery, state: FSMContext):
    optimization_id = int(callback_query.data.split(":", 1)[1])
    optimizations_db.set_active_optimization(callback_query.from_user.id, optimization_id)
    await _send_or_edit(
        callback_query,
        "Which plot do you want?",
        reply_markup=_plot_type_keyboard(optimization_id),
    )
    await state.set_state(PlotFlow.selecting_plot_type)
    await callback_query.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("plot_type:"))
async def process_plot_type(callback_query: CallbackQuery, state: FSMContext):
    _, optimization_id, plot_type = callback_query.data.split(":", 2)
    optimization_id = int(optimization_id)
    await callback_query.answer("Rendering plot...")

    try:
        if plot_type == "probability":
            paths = [render_probability_plot(optimizations_db, callback_query.from_user.id, optimization_id)]
        elif plot_type == "distribution":
            paths = [render_distribution_plot(optimizations_db, callback_query.from_user.id, optimization_id)]
        elif plot_type == "timeline":
            paths = [render_timeline_plot(optimizations_db, callback_query.from_user.id, optimization_id)]
        else:
            paths = render_all_plots(optimizations_db, callback_query.from_user.id, optimization_id)
    except ValueError as exc:
        await _send_or_edit(callback_query, str(exc))
        await state.clear()
        return

    try:
        for path in paths:
            if callback_query.message:
                await callback_query.message.answer_photo(FSInputFile(path))
            else:
                await bot.send_photo(callback_query.from_user.id, FSInputFile(path))
    finally:
        for path in paths:
            if os.path.exists(path):
                os.remove(path)

    await state.clear()


@dp.message(Command("options"))
async def options_command(message: Message):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    if optimization_id is None:
        await message.answer("No active decision yet. Send /recommend to choose one, or /setup to create one.")
        return

    optimization = optimizations_db.get_optimization_config(
        optimization_id,
        user_id=message.from_user.id,
    )
    variants = optimizations_db.get_variants_by_optimization_id(optimization_id)
    await message.answer(_format_options(optimization, variants))


@dp.message(Command("add_option"))
async def add_option_command(message: Message, state: FSMContext):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    if optimization_id is None:
        await message.answer("No active decision yet. Send /recommend to choose one, or /setup to create one.")
        return

    optimization = optimizations_db.get_optimization_config(
        optimization_id,
        user_id=message.from_user.id,
    )
    await state.update_data(option_optimization_id=optimization_id)
    await state.set_state(OptionManagement.waiting_for_variant_name)
    await message.answer(f"Send the new option name for '{optimization['optimization_name']}'.")


@dp.message(OptionManagement.waiting_for_variant_name)
async def process_added_option(message: Message, state: FSMContext):
    variant_name = message.text.strip()
    if not variant_name or variant_name.startswith("/"):
        await message.answer("Send a plain option name, or /cancel.")
        return

    data = await state.get_data()
    optimization_id = data["option_optimization_id"]
    existing = optimizations_db.get_variants_by_optimization_id(optimization_id)
    if any(row[1] == variant_name for row in existing):
        await message.answer("That option already exists. Send another name, or /cancel.")
        return

    optimizations_db.add_variant_by_id(optimization_id, variant_name)
    await state.clear()
    await message.answer(f"Added option: {variant_name}.")


@dp.message(Command("remove_option"))
async def remove_option_command(message: Message):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    if optimization_id is None:
        await message.answer("No active decision yet. Send /recommend to choose one, or /setup to create one.")
        return

    variants = optimizations_db.get_variants_by_optimization_id(optimization_id)
    if not variants:
        await message.answer("This decision has no options to remove.")
        return

    await message.answer(
        "Which option should I remove?",
        reply_markup=_variant_keyboard("remove_variant", variants, optimization_id),
    )


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("remove_variant:"))
async def process_remove_option(callback_query: CallbackQuery):
    _, optimization_id, variant_id = callback_query.data.split(":", 2)
    optimization_id = int(optimization_id)
    variant_id = int(variant_id)
    variant = optimizations_db.get_variant(variant_id, optimization_id=optimization_id)
    if variant is None:
        await _send_or_edit(callback_query, "That option no longer exists.")
        await callback_query.answer()
        return

    optimizations_db.remove_variant_by_id(optimization_id, variant_id)
    await _send_or_edit(callback_query, f"Removed option: {variant['variant_name']}.")
    await callback_query.answer()


@dp.message(Command("settings"))
async def settings_command(message: Message):
    optimization_id = get_active_or_only_optimization_id(
        optimizations_db,
        message.from_user.id,
    )
    if optimization_id is None:
        await message.answer("No active decision yet. Send /setup to create one.")
        return

    optimization = optimizations_db.get_optimization_config(
        optimization_id,
        user_id=message.from_user.id,
    )
    variants = optimizations_db.get_variants_by_optimization_id(optimization_id)
    option_names = ", ".join(variant_name for _, variant_name, _ in variants) or "none"
    await message.answer(
        f"<b>{html.escape(optimization['optimization_name'])}</b>\n"
        f"Metric: {optimization['metric_type']}\n"
        f"Objective: {optimization['objective']}\n"
        f"History: {optimization['recency_days']} days\n"
        f"Risk tolerance: {optimization['rho']}\n"
        f"Options: {html.escape(option_names)}"
    )


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("settings_for:"))
async def process_settings_for(callback_query: CallbackQuery):
    optimization_id = int(callback_query.data.split(":", 1)[1])
    optimization = optimizations_db.get_optimization_config(
        optimization_id,
        user_id=callback_query.from_user.id,
    )
    variants = optimizations_db.get_variants_by_optimization_id(optimization_id)
    option_names = ", ".join(variant_name for _, variant_name, _ in variants) or "none"
    await _send_or_edit(
        callback_query,
        f"<b>{html.escape(optimization['optimization_name'])}</b>\n"
        f"Metric: {optimization['metric_type']}\n"
        f"Objective: {optimization['objective']}\n"
        f"History: {optimization['recency_days']} days\n"
        f"Risk tolerance: {optimization['rho']}\n"
        f"Options: {html.escape(option_names)}",
    )
    await callback_query.answer()


@dp.message(
    StateFilter(None),
    lambda message: message.text
    and message.text.lower().strip() in {"hi", "hello", "hey", "what should i choose?"},
)
async def greeting_recommendation(message: Message, state: FSMContext):
    await recommend_command(message, state)
