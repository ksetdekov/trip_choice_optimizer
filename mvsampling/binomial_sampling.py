import pandas as pd
from scipy.stats import beta
from datetime import timedelta, datetime
from dataclasses import dataclass, field
import logging

@dataclass
class BinomialBandit:
    options_list: list
    minimize: bool = True
    bandit: pd.DataFrame = field(init=False)
    history: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=['option', 'reward']))

    def __post_init__(self):
        # Initialize each arm with a Beta(1,1) prior and 0 runs.
        self.bandit = pd.DataFrame({
            'name': self.options_list,
            'alpha': 1.0,  # successes count + 1
            'beta': 1.0,   # failures count + 1
            'runs': 0      # number of trials
        })

    def update_arm(self, name, reward):
        """
        Update the Beta distribution for the arm specified by name.
        For a binomial bandit, reward should be either 0 (failure) or 1 (success).
        """
        if reward not in [0, 1]:
            raise ValueError('Reward must be 0 or 1 for binomial bandit.')
        # Look up the current parameters.
        row = self.bandit[self.bandit.name == name]
        if row.empty:
            raise ValueError(f"Option '{name}' not found.")
        current_alpha = float(row['alpha'].iloc[0])
        current_beta = float(row['beta'].iloc[0])
        current_runs = int(row['runs'].iloc[0])
        # Update: add reward to alpha and (1-reward) to beta.
        new_alpha = current_alpha + reward
        new_beta = current_beta + (1 - reward)
        new_runs = current_runs + 1
        # Record this event in history.
        self.history.loc[len(self.history.index)] = [name, reward]
        # Update the bandit's DataFrame.
        self.bandit.loc[self.bandit.name == name, 'alpha'] = new_alpha
        self.bandit.loc[self.bandit.name == name, 'beta'] = new_beta
        self.bandit.loc[self.bandit.name == name, 'runs'] = new_runs

    def grade(self):
        """
        Sample from the Beta distributions for each arm and sort them.
        - If minimizing (e.g. cost or loss), lower sampled values are preferred,
          so the arms are sorted in ascending order.
        - If maximizing (e.g. rewards), higher sampled values are preferred,
          so the arms are sorted in descending order.
        """
        df = self.bandit.copy()
        df['theta_sample'] = df.apply(lambda row: beta.rvs(a=row['alpha'], b=row['beta']), axis=1)
        if self.minimize:
            # For minimization problems, sort in ascending order.
            sorted_df = df.sort_values(by='theta_sample', ascending=True)
        else:
            # For maximization problems, sort in descending order.
            sorted_df = df.sort_values(by='theta_sample', ascending=False)
        return sorted_df

    def process_events(self, events, days=91):
        """
        Process events to update the bandit.
        
        events: dict mapping datetime -> tuple(option, reward)
                where reward is 0 or 1.
        days: only events within the last 'days' days are considered.
        
        If no valid events are provided, simply return the graded state.
        """
        if not events:
            return self.grade()
        # Set threshold relative to now.
        threshold = datetime.now() - timedelta(days=days)
        filtered_events = {dt: data for dt, data in events.items() if dt >= threshold}
        logging.debug("Filtered events: %s", filtered_events)
        if filtered_events:
            for dt, (option, reward) in filtered_events.items():
                self.update_arm(option, reward)
        # Return the current graded state after processing.
        return self.grade()

    def __str__(self):
        return repr(self.bandit)