# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from pyod.models.knn import KNN
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime

# Load in data
# Get data paths
path = None
while path == None or len(path) < 5:
    path = input("Path to input file: ")

try:
    export_path = input("Output file path (default: current folder): ")
except:
    export_path = ""

# Read in data
initial_df = pd.read_csv(path)

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

        # Fields from processing
        "TDD",
        "bgs_before",
        "bgs_after",
        "before_event_strings",
        "after_event_strings",
        "bgInput"
    ]
]
type_map = {"temp": 0}

df = df.replace({"deliveryType": type_map})
# Filter to get temp basals
df = df.loc[(df["type"] == 0) & (df["deliveryType"] == 0)]
# Drop if any values are NaN
df = df.dropna()
# Convert the time strings to pandas datetime format
df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True)

# Print some summary statistics
print("Head")
print(df.head(), "\n")
shape = df.shape
print("Shape", shape)
print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

# will want to play around with n_neighbors
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

# Export the data
time = datetime.now().strftime("%H_%M_%S")
file_name = "abnormal_basals_" + time
abnormals.to_csv(export_path + file_name + ".csv")