import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import stumpy

from pathlib import Path
from scipy.signal import savgol_filter


from matplotlib.patches import Rectangle

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
bgs["derivative"] = savgol_filter(bgs["log_bg"], 15, 13, deriv=1)

m = 20
mp = stumpy.stump(bgs["derivative"], m)

fig, axs = plt.subplots(3, sharex=True, gridspec_kw={'hspace': 0})
plt.suptitle('Motif (Pattern) Discovery', fontsize='30')

abnormal_location = np.argwhere(mp[:, 0] == mp[:, 0].max()).flatten()[0]

axs[0].plot(bgs["value"].values)
rect = Rectangle((abnormal_location, 0), m, 100, facecolor='lightgrey')
axs[0].add_patch(rect)
axs[1].set_ylabel("BG Value", fontsize='10')
axs[1].plot(bgs["derivative"].values)
axs[1].set_ylabel("Rate of Change", fontsize='10')
axs[2].plot(mp[:, 0])
axs[2].set_ylabel("Matrix Profile", fontsize='10')
plt.show()