from aiogram.fsm.state import StatesGroup, State

class NewOptimization(StatesGroup):
    waiting_for_name = State()
    waiting_for_type = State() 

class NewVariant(StatesGroup):
    waiting_for_optimization_name = State()
    waiting_for_variant_name = State()
    
class NewOptionValue(StatesGroup):
    waiting_for_value = State()


class SetupOptimization(StatesGroup):
    waiting_for_name = State()
    waiting_for_metric_type = State()
    waiting_for_objective = State()
    waiting_for_recency = State()
    waiting_for_rho = State()
    waiting_for_variants = State()


class RecommendationFlow(StatesGroup):
    selecting_optimization = State()


class LogObservation(StatesGroup):
    selecting_optimization = State()
    selecting_variant = State()
    waiting_for_value = State()


class PlotFlow(StatesGroup):
    selecting_optimization = State()
    selecting_plot_type = State()


class OptionManagement(StatesGroup):
    waiting_for_variant_name = State()
