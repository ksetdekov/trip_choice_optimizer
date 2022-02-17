import pandas as pd
import numpy as np

def to_minutes(timestr: str):
    '''
    convert timestr to float minutes
    '''
    return pd.to_timedelta(timestr).total_seconds()/60

class HandsTable():
    def __init__(self) -> None:
        pass

    def update_mean(X, T_last, mu_last):
        mu_new = T_last * mu_last / (T_last + 1) + X / (T_last + 1)
        return mu_new

    def update_samples(T):
        return T + 1

    def update_shape(a):
        return a + 0.5

    def update_rate(X, mu_last, beta_last, T_last):
        beta_new = beta_last + (T_last / (T_last + 1)) * (np.square(X - mu_last)) / 2
        return beta_new
