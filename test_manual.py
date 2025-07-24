import unittest
import pandas as pd
from datetime import datetime, timedelta
from mvsampling.binomial_sampling import BinomialBandit

options = ['A', 'B']
bandit = BinomialBandit(options)
now = datetime.now()
events = {
    now - timedelta(days=10): ('A', 1),
    now - timedelta(days=8): ('A', 1),  
    now - timedelta(days=6): ('A', 1),
    now - timedelta(days=4): ('A', 1),
    now - timedelta(days=2): ('A', 1),
    now - timedelta(days=1): ('B', 0),
    now - timedelta(days=9): ('B', 0),
    now - timedelta(days=5): ('B', 0),
    now - timedelta(days=3): ('B', 0)
}

result = bandit.process_events(events, days=91)
print(result)