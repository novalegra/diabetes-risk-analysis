# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from pyod.models.knn import KNN
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D

# Load in data
path = str(Path(__file__).parent.parent)
initial_df = pd.read_csv(path + "/data/risk-data-sample.csv")

df = initial_df[
    [
        # Categorical
        "type", # type of data: CBG, basal, bolus, etc
        "deliveryType", # type of basal: scheduled (according to programmed basal schedule) vs temp

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
print("Shape", df.shape)
print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

# will want to play around with n_neighbors
model = KNN()
model.fit(df)

predictions = model.predict(df)
unique, counts = np.unique(predictions, return_counts=True)
print ("Outliers:", unique.length, "\nTotal:", counts.length, "\n Percent:", unique.length/counts.length * 100)
#print(dict(zip(unique, counts)))

fig = plt.figure(1, figsize=(7,7))
ax = Axes3D(fig, rect=[0, 0, 0.95, 1], elev=48, azim=134)
ax.scatter(df["duration"], df["percent"], df["rate"],
        c=predictions, edgecolor="k", s=50)
ax.set_xlabel("Duration")
ax.set_ylabel("Percent")
ax.set_zlabel("Rate")
plt.title("KNN To Classify Temp Basals", fontsize=14)
plt.show()