# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from pyod.models.knn import KNN
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime

from bolus_risk_analysis import find_bgs

# Load in data
path = str(Path(__file__).parent.parent)
initial_df = pd.read_csv(path + "/data/risk-data-sample.csv")

# Get a dataframe with only the BG values
bgs = initial_df[
    [
        # Categorical
        "type", # type of data: CBG, basal, bolus, etc
        "time",

        # Numerical
        "value" # BG reading in mmol/L
    ]
]
bg_map = {"cbg": 2}
bgs = bgs.replace({"type": bg_map})
bgs = bgs.loc[(bgs["type"] == 2)]
bgs.dropna(inplace=True)
bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)

df = initial_df[
    [
        # Categorical
        "type", # type of data: CBG, basal, bolus, etc
        "deliveryType", # type of basal: scheduled (according to programmed basal schedule) vs temp
        "time",

        # Numerical
        "duration", # temp basal length
        "percent", # percent of basal rate
        "rate", # absolute basal rate
    ]
]
basal_map = {"basal": 0}
type_map = {"temp": 0}

df = df.replace({"type": basal_map, "deliveryType": type_map})
# Filter to get temp basals
df = df.loc[(df["type"] == 0) & (df["deliveryType"] == 0)]
# Drop if any values are NaN
df = df.dropna()

# Print some summary statistics
print("Head")
print(df.head(), "\n")
shape = df.shape
print("Shape", shape)
print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

# will want to play around with n_neighbors
print(df.columns)
model = KNN()
model.fit(df[["duration", "percent", "rate"]])

predictions = model.predict(df[["duration", "percent", "rate"]])
df["abnormal"] = predictions
unique, counts = np.unique(predictions, return_counts=True)
print ("Outliers:", counts[1], "\nTotal:", shape[0], "\n Percent:", round(counts[1]/shape[0] * 100), "%")

# Plot results
fig = plt.figure(1, figsize=(7,7))
ax = Axes3D(fig, rect=[0, 0, 0.95, 1], elev=48, azim=134)
ax.scatter(df["duration"], df["percent"], df["rate"],
        c=predictions, edgecolor="k", s=50)
ax.set_xlabel("Duration")
ax.set_ylabel("Percent")
ax.set_zlabel("Rate")
plt.title("KNN To Classify Temp Basals", fontsize=14)
plt.show()

# Select our abnormal rows
abnormals = df.query('abnormal == 1')
abnormals = abnormals.sort_values("time")
abnormals["bgs_before"] = abnormals["time"].apply(find_bgs, args=(120, 5))
abnormals["bgs_after"] = abnormals["time"].apply(find_bgs, args=(5, 120))

time = datetime.now().strftime("%H_%M_%S")
file_name = "abnormal_basals_" + time
abnormals.to_csv(file_name + ".csv")