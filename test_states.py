import unittest
from aiogram.fsm.state import State
from states import (
    LogObservation,
    NewOptimization,
    NewOptionValue,
    NewVariant,
    OptionManagement,
    PlotFlow,
    RecommendationFlow,
    SetupOptimization,
)

class TestStates(unittest.TestCase):
    def test_new_optimization_state(self):
        state = NewOptimization.waiting_for_name
        self.assertIsInstance(state, State)
        # Check that the state's qualified name includes the class name.
        self.assertIn("NewOptimization", state.state) # type: ignore

    def test_new_variant_states(self):
        state_opt = NewVariant.waiting_for_optimization_name
        state_var = NewVariant.waiting_for_variant_name
        self.assertIsInstance(state_opt, State)
        self.assertIsInstance(state_var, State)
        # States must be distinct.
        self.assertNotEqual(state_opt, state_var)
        self.assertIn("NewVariant", state_opt.state) # type: ignore
        self.assertIn("NewVariant", state_var.state) # type: ignore

    def test_new_option_value_state(self):
        state = NewOptionValue.waiting_for_value
        self.assertIsInstance(state, State)
        self.assertIn("NewOptionValue", state.state) # type: ignore

    def test_setup_optimization_states(self):
        states = [
            SetupOptimization.waiting_for_name,
            SetupOptimization.waiting_for_metric_type,
            SetupOptimization.waiting_for_objective,
            SetupOptimization.waiting_for_recency,
            SetupOptimization.waiting_for_rho,
            SetupOptimization.waiting_for_variants,
        ]
        self.assertEqual(len({state.state for state in states}), len(states)) # type: ignore
        for state in states:
            self.assertIsInstance(state, State)
            self.assertIn("SetupOptimization", state.state) # type: ignore

    def test_daily_flow_states(self):
        states = [
            RecommendationFlow.selecting_optimization,
            LogObservation.selecting_optimization,
            LogObservation.selecting_variant,
            LogObservation.waiting_for_value,
            PlotFlow.selecting_optimization,
            PlotFlow.selecting_plot_type,
            OptionManagement.waiting_for_variant_name,
        ]
        self.assertEqual(len({state.state for state in states}), len(states)) # type: ignore
        for state in states:
            self.assertIsInstance(state, State)

if __name__ == '__main__':
    unittest.main()
