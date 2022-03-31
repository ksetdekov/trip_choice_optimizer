import mvsampling.mvsampling as mv # The code to test
import pandas as pd
import unittest   # The test framework

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
                            'mu': {0: 75, 1: 95},
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


if __name__ == '__main__':
    unittest.main()
