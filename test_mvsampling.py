import unittest  # The test framework

import pandas as pd
from datetime import datetime, timedelta
import unittest

import mvsampling.mvsampling as mv  # The code to test


class Test_TestIncrementDecrement(unittest.TestCase):
    def test_has_needed_columns(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        a.update_hands('2', 100)
        a.update_hands('2', 90)
        a.update_hands('1', 80)
        a.update_hands('1', 70)
        b = a.grade()
        self.assertTrue(b.columns.isin(['name', 'mu', 'Te', 'alpha', 'beta', 'tau', 'theta', 'SD', 'var95']).all())

    def test_df_hands_correct_df(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        a.update_hands('2', 100)
        a.update_hands('2', 90)
        a.update_hands('1', 80)
        a.update_hands('1', 70)
        correct_hand  = pd.DataFrame({'name': {0: '1', 1: '2'},
                            'mu': {0: 75.0, 1: 95.0},
                            'Te': {0: 2, 1: 2},
                            'alpha': {0: 1.5, 1: 1.5},
                            'beta': {0: 25.5, 1: 25.5}})
        self.assertTrue(a.hands.equals(correct_hand))

    def test_different_every_time(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        a.update_hands('2', 100)
        a.update_hands('2', 90)
        a.update_hands('1', 80)
        a.update_hands('1', 70)
        b = a.grade()
        c = a.grade()
        self.assertFalse(b.equals(c))

    def test_update_shape(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        b = a.update_shape(10)
        self.assertEquals(b, 10.5)


    def test_process_events(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        events = {
            datetime.now() - timedelta(days=1): ('1', 100),
            datetime.now() - timedelta(days=2): ('2', 90),
            datetime.now() - timedelta(days=100): ('1', 80),
            datetime.now() - timedelta(days=200): ('2', 70)
        }
        result = a.process_events(events)
        self.assertTrue(result.columns.isin(
            ['name', 'mu', 'Te', 'alpha', 'beta', 'tau', 'theta', 'SD', 'var95']).all())
        self.assertTrue('1' in result['name'].values)
        self.assertTrue('2' in result['name'].values)

    # Additional tests
    def test_to_minutes(self):
        minutes = mv.HandsTable.to_minutes("00:45:00")
        self.assertAlmostEqual(minutes, 45.0)

    def test_invalid_time_string(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        with self.assertRaises(ValueError):
            a.update_hands('1', "invalid_time")

    def test_update_rate_and_mean(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        original = a.hands[a.hands.name == '1'].iloc[0]
        # use a numeric value to update
        a.update_hands('1', 50)
        updated = a.hands[a.hands.name == '1'].iloc[0]
        expected_mu = mv.HandsTable.update_mean(50, original['Te'], original['mu'])
        self.assertAlmostEqual(updated['mu'], expected_mu)

    def test_history_update(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        self.assertTrue(a.history.empty)
        a.update_hands('1', 100)
        self.assertFalse(a.history.empty)
        self.assertIn('1', a.history['option'].values)
        self.assertIn(100, a.history['value'].values)

    def test_str_method(self):
        a = mv.HandsTable(['1', '2'], minimize=False)
        a.update_hands('1', 100)
        rep = str(a)
        self.assertIn("1", rep)
        self.assertIn("mu", rep)

    def test_grade_minimize_true_mu_zero(self):
        """
        Test the branch in grade() when minimize is True and the minimum of mu is 0.
        It should compute 'var95' and reorder output based on increasing Te.
        """
        # Create a HandsTable instance with initial mu=0 for all options.
        ht = mv.HandsTable(['A', 'B'], minimize=True)
        # Get the graded DataFrame.
        result = ht.grade()
        # Check that 'var95' column exists.
        self.assertIn('var95', result.columns)
        
        # Since initial mu values are 0, the branch should use ordering based on Te.
        # Extract Te column and verify it's in non-decreasing order.
        Te_values = result['Te'].to_list()
        self.assertEqual(Te_values, sorted(Te_values))
    
    def test_grade_minimize_true_nonzero_mu(self):
        """
        Test the branch in grade() when minimize is True and mu has been updated (non-zero).
        It should compute 'var95' and reorder output based on self.rho * theta_drops + 1/tau.
        Since the evaluation is based on random sampling, we check for column existence.
        """
        ht = mv.HandsTable(['A', 'B'], minimize=True)
        # Manually set mu values to non-zero to force the else branch.
        ht.hands['mu'] = [1.0, 1.0]
        result = ht.grade()
        # Validate that 'var95' column exists.
        self.assertIn('var95', result.columns)
        # We can also check that the number of rows remains the same.
        self.assertEqual(len(result), len(ht.hands))
    
    def test_grade_minimize_false(self):
        """
        Test the branch in grade() when minimize is False.
        It should compute 'var95' accordingly and order the DataFrame.
        """
        ht = mv.HandsTable(['A', 'B'], minimize=False)
        # Set mu to non-zero values to force the else branch.
        ht.hands['mu'] = [1.0, 2.0]
        result = ht.grade()
        # Check that 'var95' exists.
        self.assertIn('var95', result.columns)
        # Ensure the output DataFrame has the correct number of rows.
        self.assertEqual(len(result), len(ht.hands))


if __name__ == '__main__':
    unittest.main()
