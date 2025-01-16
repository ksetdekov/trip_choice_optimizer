from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy.stats import gamma, norm


@dataclass
class HandsTable:
    minimize: bool = True
    rho: float = 1.0
    hands: pd.DataFrame = field(default_factory=lambda: pd.DataFrame({
        'name': [],
        'mu': [],
        'Te': [],
        'alpha': [],
        'beta': []
    }))
    history: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=['option', 'value']))

    @staticmethod
    def to_minutes(timestr: str) -> float:
        """
        Convert a time string in the format 'hh:mm:ss' to minutes as a float.
        """
        return pd.to_timedelta(timestr).total_seconds() / 60

    @staticmethod
    def update_mean(X: float, T_last: float, mu_last: float) -> float:
        """
        Update the mean of the data.
        """
        return T_last * mu_last / (T_last + 1) + X / (T_last + 1)

    @staticmethod
    def update_samples(T: float) -> float:
        """
        Increment the sample size.
        """
        return T + 1

    @staticmethod
    def update_shape(alpha: float) -> float:
        """
        Update the shape parameter of the gamma distribution.
        """
        return alpha + 0.5

    @staticmethod
    def update_rate(X: float, mu_last: float, beta_last: float, T_last: float) -> float:
        """
        Update the rate parameter of the gamma distribution.
        """
        return beta_last + (T_last / (T_last + 1)) * (np.square(X - mu_last)) / 2

    def update_hands(self, name: str, value: float) -> None:
        """
        Update the statistics for a given option (hand).
        """
        value = self._convert_value(value)
        self._update_hand_stats(name, value)
        self._log_history(name, value)

    def _convert_value(self, value: float) -> float:
        """
        Convert input value to float. Supports time strings and numeric values.
        """
        if isinstance(value, str):
            return self.to_minutes(value)
        elif isinstance(value, (int, float)):
            return float(value)
        else:
            raise ValueError("Input must be a time string or a numeric value.")

    def _update_hand_stats(self, name: str, value: float) -> None:
        """
        Update the parameters for a specific hand.
        """
        hand_row = self.hands.loc[self.hands.name == name]
        if hand_row.empty:
            raise ValueError(f"Option '{name}' not found.")

        mu, t, alpha, beta = hand_row[['mu', 'Te', 'alpha', 'beta']].values[0]
        beta = self.update_rate(value, mu, beta, t)
        mu = self.update_mean(value, t, mu)
        t = self.update_samples(t)
        alpha = self.update_shape(alpha)

        self.hands.loc[self.hands.name == name, ['mu', 'Te', 'alpha', 'beta']] = [mu, t, alpha, beta]

    def _log_history(self, name: str, value: float) -> None:
        """
        Log the history of updates.
        """
        self.history.loc[len(self.history)] = {'option': name, 'value': value}

    def grade(self) -> pd.DataFrame:
        """
        Rank the options based on Bayesian updates and risk tolerance.
        Returns a DataFrame with updated statistics and rankings.
        """
        hands_output = self.hands.copy()
        hands_output['tau'] = gamma.rvs(a=hands_output.alpha, scale=1 / hands_output.beta)
        hands_output['SD'] = np.sqrt(1 / hands_output['tau'])
        hands_output['theta'] = norm.rvs(hands_output.mu, 1 / hands_output.Te)

        confidence_level = 0.05
        hands_output['ci95'] = hands_output['theta'] + norm.ppf(1 - confidence_level / 2) * hands_output['SD']

        if self.minimize:
            hands_output = hands_output.sort_values(by=self.rho * hands_output['theta'] + 1 / hands_output['tau'])
        else:
            hands_output = hands_output.sort_values(by=self.rho * hands_output['theta'] - 1 / hands_output['tau'], ascending=False)

        return hands_output

    def __repr__(self) -> str:
        """
        Provide a readable representation of the HandsTable instance.
        """
        return (
            f"HandsTable(minimize={self.minimize}, rho={self.rho})\n"
            f"Hands:\n{self.hands}\n"
            f"History:\n{self.history}"
        )
