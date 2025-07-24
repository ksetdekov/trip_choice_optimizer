import unittest
from aiogram.fsm.state import State
from states import NewOptimization, NewVariant, NewOptionValue

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

if __name__ == '__main__':
    unittest.main()