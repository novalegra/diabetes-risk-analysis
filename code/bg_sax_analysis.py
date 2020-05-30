import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pathlib import Path
from scipy.stats import norm
from sklearn.preprocessing import StandardScaler

# Constants
all_alphabet = "abcdefghijklmnopqrstuvwxyz"

def get_sax_encodings(bgs, alphabet_size=7, bin_time_interval = "10min"):
    # Normalize the BG values
    bgs["normalized_log_bg"] = (bgs["log_bg"] - bgs["log_bg"].mean()) / bgs["log_bg"].std(ddof=0)

    # Get the Piecewise Aggregate Approximation (PAA)
    averaged_times = bgs.groupby(pd.Grouper(key="time", freq=bin_time_interval)).mean().reset_index()

    # Get breakpoints
    breakpoints = norm.ppf(np.linspace(0, 1, alphabet_size + 1)[1:-1])
    breakpoints = np.insert(breakpoints, 0, -np.inf)
    breakpoints = np.append(breakpoints, np.inf)
    alphabet = list(all_alphabet[0:alphabet_size])
    nan_letter = all_alphabet[alphabet_size:alphabet_size + 1]

    # Assign letter to each value in time series
    averaged_times["bin"] = pd.cut(
        averaged_times["normalized_log_bg"],
        breakpoints,
        labels=alphabet
    )

    # Assign letter to missing data points
    averaged_times["bin"] = averaged_times["bin"].cat.add_categories(nan_letter)
    averaged_times["bin"].fillna(nan_letter, inplace=True)

    return averaged_times