import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pathlib import Path
from scipy.stats import norm
from sklearn.preprocessing import StandardScaler


all_alphabet = "abcdefghijklmnopqrstuvwxyz"

# Load data and bin
path = str(Path(__file__).parent.parent)
bgs = pd.read_csv(path + "/data/risk-data-sample.csv")[
    [
        # Categorical
        "type", # type of data: CBG, basal, bolus, etc
        "time", # time of measurement

        # Numerical
        "value" # BG reading in mmol/L
    ]
]
# Extract a dataframe with only the BG values
bg_map = {"cbg": 2}
bgs = bgs.replace({"type": bg_map})
bgs = bgs.loc[(bgs["type"] == 2)]
bgs.dropna(inplace=True)
bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)

# Take log of BG values
bgs["log_bg"] = np.log10(bgs["value"])

# Normalize the BG values
bgs["normalized_log_bg"] = (bgs["log_bg"] - bgs["log_bg"].mean()) / bgs["log_bg"].std(ddof=0)

# Get the Piecewise Aggregate Approximation (PAA)
ten_min_avg = bgs.groupby(pd.Grouper(key="time", freq="10min")).mean().reset_index()
half_hour_avg = bgs.groupby(pd.Grouper(key="time", freq="30min")).mean().reset_index()
hour_avg = bgs.groupby(pd.Grouper(key="time", freq="60min")).mean().reset_index()
three_hour_avg = bgs.groupby(pd.Grouper(key="time", freq="180min")).mean().reset_index()

# Get breakpoints
alphabet_size = 7
breakpoints = norm.ppf(np.linspace(0, 1, alphabet_size + 1)[1:-1])
breakpoints = np.insert(breakpoints, 0, -np.inf)
breakpoints = np.append(breakpoints, np.inf)
alphabet = list(all_alphabet[0:alphabet_size])

ten_min_avg["bin"] = pd.cut(
    ten_min_avg["normalized_log_bg"],
    breakpoints,
    labels=alphabet
)

half_hour_avg["bin"] = pd.cut(
    half_hour_avg["normalized_log_bg"],
    breakpoints,
    labels=alphabet
)

hour_avg["bin"] = pd.cut(
    hour_avg["normalized_log_bg"],
    breakpoints,
    labels=alphabet
)

three_hour_avg["bin"] = pd.cut(
    three_hour_avg["normalized_log_bg"],
    breakpoints,
    labels=alphabet
)

ten_min_avg.to_csv("ten_min_avg" + ".csv")
half_hour_avg.to_csv("half_hour_avg" + ".csv")
hour_avg.to_csv("hour_avg" + ".csv")
three_hour_avg.to_csv("three_hour_sax" + ".csv")