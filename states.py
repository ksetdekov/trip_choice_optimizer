from aiogram.fsm.state import StatesGroup, State

class NewOptimization(StatesGroup):
    waiting_for_name = State()

class NewVariant(StatesGroup):
    waiting_for_optimization_name = State()
    waiting_for_variant_name = State()
class NewOptionValue(StatesGroup):
    waiting_for_value = State()