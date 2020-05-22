# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from pyod.models.knn import KNN
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime

# Load in data
path = str(Path(__file__).parent.parent)
initial_df = pd.read_csv(path + "/data/risk-data-sample.csv")
df = initial_df[
    [
        # Categorical
        "type", # type of data: CBG, basal, bolus, etc
        "time",
        #"subType" # subtype of bolus: normal, extended, dual wave

        # Numerical
        "normal", # units delivered via a "normal" bolus
        "extended", # units delivered via an extended bolus
        "insulinCarbRatio", 
        "carbInput", # number of carbs input into bolus calculator
        "insulinOnBoard",
        "bgInput",
        "insulinSensitivity"
    ]
]
bolus_map = {"bolus": 1}
df.replace({"type": bolus_map}, inplace=True)
df.fillna({"carbInput": 0, "normal": 0, "extended": 0}, inplace=True)

# Filter to get boluses
df = df.loc[(df["type"] == 1),]
df["totalAmount"] = df["normal"] + df["extended"]
# Drop if any values are NaN
df = df.dropna(subset=["totalAmount", "insulinCarbRatio"])

# Print some summary statistics
print("Head")
print(df.head(), "\n")
shape = df.shape
print("Shape", shape)
print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

# will want to play around with n_neighbors
model = KNN()
model.fit(df[["totalAmount", "carbInput", "insulinCarbRatio"]])

predictions = model.predict(df[["totalAmount", "carbInput", "insulinCarbRatio"]])
df["abnormal"] = predictions
unique, counts = np.unique(predictions, return_counts=True)
print ("Outliers:", counts[1], "\nTotal:", shape[0], "\n Percent:", round(counts[1]/shape[0] * 100), "%")

# Export our abnormal rows
df = df.query('abnormal == 1')
df.sort_values("time", inplace=True)
time = datetime.now().strftime("%H:%M:%S")
path = "abnormal_boluses_" + time + ".csv"
df.to_csv(path)

'''# Plot the results
fig = plt.figure(1, figsize=(7,7))
ax = Axes3D(fig, rect=[0, 0, 0.95, 1], elev=48, azim=134)
ax.scatter(df["totalAmount"], df["carbInput"], df["insulinCarbRatio"],
        c=predictions, edgecolor="k", s=50)
ax.set_xlabel("Bolus Amount")
ax.set_ylabel("Carb Amount")
ax.set_zlabel("CR")
plt.title("KNN To Classify Boluses", fontsize=14)
plt.show()