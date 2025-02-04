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


if __name__ == '__main__':
    unittest.main()
