import pandas as pd
import numpy as np


class HandsTable():
    def __init__(self, options_list):
        self.hands = pd.DataFrame({'name': options_list,
                                   'mu': 0, 
                                   'Te': 0, 
                                   'alpha': 0.5, 
                                   'beta': 0.5
                                   })
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
        beta_new = beta_last + (T_last / (T_last + 1)) * (np.square(X - mu_last)) / 2
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
        print(f'value{value}, mu{mu}, beta{beta}, t{t}')
        beta = HandsTable.update_rate(value, mu, beta, t)
        mu =  HandsTable.update_mean(value, t, mu)
        t = HandsTable.update_samples(t)
        alpha = HandsTable.update_shape(alpha)

        self.hands.loc[self.hands.name == name, 'mu'] = mu
        self.hands.loc[self.hands.name == name, 'Te'] = t
        self.hands.loc[self.hands.name == name, 'alpha'] = alpha
        self.hands.loc[self.hands.name == name, 'beta'] = beta

    def __str__(self):
        return repr(self.hands)

a = HandsTable(['1, ', '2'])

print(a)

a.update_hands('2', 100)
print(a)
