from curses import def_prog_mode
import pandas as pd
import numpy as np
from scipy.stats import gamma, norm


class HandsTable():
    minimize = True
    rho = 3.37

    def __init__(self, options_list, minimize=True, rho=1.0):
        """инициализация

        Args:
            options_list (list): список из названий
            minimize (bool, optional): Минимизировать если True, максимизировать если False. Defaults to True.
            rho (float, optional): Риск толерантность, чем больше, тем больше риска готовы принять. Defaults to 1.0.
        """
        self.hands = pd.DataFrame({'name': options_list,
                                   'mu': 0,
                                   'Te': 0,
                                   'alpha': 0.5,
                                   'beta': 0.5
                                   })
        self.minimize = minimize
        if rho is not None:
            self.rho = rho

        self.history = pd.DataFrame(columns=['option', 'value'])

    @classmethod
    def to_minutes(self, timestr: str):
        '''
        convert timestr to float minutes
        '''
        return pd.to_timedelta(timestr).total_seconds()/60

    @classmethod
    def update_mean(self, X, T_last, mu_last):
        mu_new = T_last * mu_last / (T_last + 1) + X / (T_last + 1)
        return mu_new

    @classmethod
    def update_samples(self, T):
        return T + 1

    @classmethod
    def update_shape(self, a):
        return a + 0.5

    @classmethod
    def update_rate(self, X, mu_last, beta_last, T_last):
        beta_new = beta_last + (T_last / (T_last + 1)) * \
            (np.square(X - mu_last)) / 2
        return beta_new

    def update_hands(self, name, value):
        if isinstance(value, str):
            try:
                value = HandsTable.to_minutes(value)
            except ValueError:
                raise ValueError('input time string in hh:mm:ss format')
        elif isinstance(value, float) or isinstance(value, int):
            pass
        else:
            raise ValueError('input time string or int/float value')

        _, mu, t, alpha, beta = self.hands[self.hands.name == name].values[0]
        beta = HandsTable.update_rate(value, mu, beta, t)
        mu = HandsTable.update_mean(value, t, mu)
        t = HandsTable.update_samples(t)
        alpha = HandsTable.update_shape(alpha)

        # added code to write history
        self.history.loc[len(self.history.index)] = [name, value]

        self.hands.loc[self.hands.name == name, 'mu'] = mu
        self.hands.loc[self.hands.name == name, 'Te'] = t
        self.hands.loc[self.hands.name == name, 'alpha'] = alpha
        self.hands.loc[self.hands.name == name, 'beta'] = beta

    def grade(self):
        hands_output = self.hands.copy()
        tau = gamma.rvs(a=hands_output.alpha, scale=1/hands_output.beta)
        theta_drops = norm.rvs(hands_output.mu, 1/hands_output.Te)
        hands_output['tau'] = tau
        hands_output['theta'] = theta_drops
        hands_output['SD'] = np.sqrt(1/tau)

        if self.minimize == True:
            hands_output['var95'] = theta_drops + \
                norm.ppf(1-0.05/2) * hands_output.SD
            if hands_output.mu.min() == 0:

                output_df = hands_output.reindex(np.argsort(hands_output.Te))
            else:
                output_df = hands_output.reindex(
                    np.argsort(self.rho * theta_drops + 1/tau))
        else:
            hands_output['var95'] = theta_drops + \
                norm.ppf(0.05/2) * hands_output.SD
            if hands_output.mu.min() == 0:
                output_df = hands_output.reindex(np.argsort(hands_output.Te))
            else:
                output_df = hands_output.reindex(
                    np.argsort(self.rho * theta_drops - 1/tau)[::-1])

        return output_df

    def __str__(self):
        return repr(self.hands)
