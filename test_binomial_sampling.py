import unittest
import pandas as pd
from datetime import datetime, timedelta
from mvsampling.binomial_sampling import BinomialBandit

class TestBinomialBandit(unittest.TestCase):

    def test_initialization(self):
        options = ['A', 'B', 'C']
        bandit = BinomialBandit(options, minimize=True)
        expected = pd.DataFrame({
            'name': options,
            'alpha': [1.0, 1.0, 1.0],
            'beta': [1.0, 1.0, 1.0],
            'runs': [0, 0, 0]
        })
        pd.testing.assert_frame_equal(bandit.bandit.reset_index(drop=True), expected)
        self.assertTrue(bandit.history.empty)

    def test_update_arm_success(self):
        options = ['A', 'B']
        bandit = BinomialBandit(options)
        bandit.update_arm('A', 1)
        row = bandit.bandit[bandit.bandit['name'] == 'A'].iloc[0]
        # After a success (reward=1), alpha increases by 1 and beta remains the same.
        self.assertEqual(row['alpha'], 2.0)
        self.assertEqual(row['beta'], 1.0)
        self.assertEqual(row['runs'], 1)
        # Check history is updated.
        self.assertEqual(len(bandit.history), 1)
        self.assertEqual(bandit.history.iloc[0].tolist(), ['A', 1])

    def test_update_arm_failure(self):
        options = ['A']
        bandit = BinomialBandit(options)
        bandit.update_arm('A', 0)
        row = bandit.bandit[bandit.bandit['name'] == 'A'].iloc[0]
        # After a failure (reward=0), beta increases by 1 and alpha remains the same.
        self.assertEqual(row['alpha'], 1.0)
        self.assertEqual(row['beta'], 2.0)
        self.assertEqual(row['runs'], 1)

    def test_update_arm_invalid_reward(self):
        options = ['A']
        bandit = BinomialBandit(options)
        with self.assertRaises(ValueError) as context:
            bandit.update_arm('A', 2)
        self.assertIn("Reward must be 0 or 1", str(context.exception))

    def test_update_arm_option_not_found(self):
        options = ['A']
        bandit = BinomialBandit(options)
        with self.assertRaises(ValueError) as context:
            bandit.update_arm('B', 1)
        self.assertIn("Option 'B' not found", str(context.exception))

    def test_grade_minimize(self):
        options = ['A', 'B']
        bandit = BinomialBandit(options, minimize=True)
        # Override parameters for predictable sampling behavior.
        bandit.bandit['alpha'] = [2.0, 1.0]
        bandit.bandit['beta'] = [1.0, 1.0]
        graded = bandit.grade()
        # Confirm that the graded DataFrame has theta_sample.
        self.assertIn('theta_sample', graded.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(graded['theta_sample']))

    def test_grade_maximize(self):
        options = ['A', 'B']
        bandit = BinomialBandit(options, minimize=False)
        bandit.bandit['alpha'] = [2.0, 1.0]
        bandit.bandit['beta'] = [1.0, 1.0]
        graded = bandit.grade()
        self.assertIn('theta_sample', graded.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(graded['theta_sample']))

    def test_process_events_filters_old_events(self):
        options = ['A', 'B']
        bandit = BinomialBandit(options)
        now = datetime.now()
        events = {
            now - timedelta(days=100): ('A', 1),   # Older than 91 days.
            now - timedelta(days=10): ('B', 0)       # Recent event.
        }
        bandit.process_events(events, days=91)
        row_A = bandit.bandit[bandit.bandit['name'] == 'A'].iloc[0]
        row_B = bandit.bandit[bandit.bandit['name'] == 'B'].iloc[0]
        # Option A should remain unchanged.
        self.assertEqual(row_A['alpha'], 1.0)
        self.assertEqual(row_A['beta'], 1.0)
        self.assertEqual(row_A['runs'], 0)
        # Option B updated (reward=0 -> beta increases by 1).
        self.assertEqual(row_B['alpha'], 1.0)
        self.assertEqual(row_B['beta'], 2.0)
        self.assertEqual(row_B['runs'], 1)

    def test_process_events_no_events(self):
        options = ['A']
        bandit = BinomialBandit(options)
        graded = bandit.process_events(None)
        row = bandit.bandit.iloc[0]
        self.assertEqual(row['alpha'], 1.0)
        self.assertEqual(row['beta'], 1.0)
        self.assertEqual(row['runs'], 0)
    
    def test_adding_10_observations(self):
        options = ['A', 'B']
        bandit = BinomialBandit(options)
        now = datetime.now()
        events = {
            now - timedelta(days=10): ('A', 1),
            now - timedelta(days=9): ('B', 0),
            now - timedelta(days=8): ('A', 1),  
            now - timedelta(days=6): ('A', 1),
            now - timedelta(days=5): ('B', 0),
            now - timedelta(days=4): ('A', 1),
            now - timedelta(days=3): ('B', 0),
            now - timedelta(days=2): ('A', 1),
            now - timedelta(days=1): ('B', 0)
        }
        bandit.process_events(events, days=91)
        row_A = bandit.bandit[bandit.bandit['name'] == 'A'].iloc[0]
        row_B = bandit.bandit[bandit.bandit['name'] == 'B'].iloc[0]
        # Check if the counts are correct.
        self.assertEqual(row_A['alpha'], 6.0)
        self.assertEqual(row_A['beta'], 1.0)
        self.assertEqual(row_A['runs'], 5)
        self.assertEqual(row_B['alpha'], 1.0)
        self.assertEqual(row_B['beta'], 5.0)
        self.assertEqual(row_B['runs'], 4)
        # Check if the history is updated correctly.
        self.assertEqual(len(bandit.history), 9)
        # B is a bad option. it shouild be on top for a default parameters.
        self.assertEqual(bandit.grade().iloc[0]['name'], 'B')

    def test_minimize_false(self):
        options = ['A', 'B']
        bandit = BinomialBandit(options, minimize=False)
        now = datetime.now()
        events = {
            now - timedelta(days=10): ('A', 1),
            now - timedelta(days=9): ('B', 0),
            now - timedelta(days=8): ('A', 1),  
            now - timedelta(days=6): ('A', 1),
            now - timedelta(days=5): ('B', 0),
            now - timedelta(days=4): ('A', 1),
            now - timedelta(days=3): ('B', 0),
            now - timedelta(days=2): ('A', 1),
            now - timedelta(days=1): ('B', 0)
        }
        bandit.process_events(events, days=91)
        row_A = bandit.bandit[bandit.bandit['name'] == 'A'].iloc[0]
        row_B = bandit.bandit[bandit.bandit['name'] == 'B'].iloc[0]
        # Check if the counts are correct.
        self.assertEqual(row_A['alpha'], 6.0)
        self.assertEqual(row_A['beta'], 1.0)
        self.assertEqual(row_A['runs'], 5)
        self.assertEqual(row_B['alpha'], 1.0)
        self.assertEqual(row_B['beta'], 5.0)
        self.assertEqual(row_B['runs'], 4)
        # Check if the history is updated correctly.
        self.assertEqual(len(bandit.history), 9)
        # A is a good option. it shouild be on top for a minimize False.
        self.assertEqual(bandit.grade().iloc[0]['name'], 'A')  

if __name__ == '__main__':
    unittest.main()