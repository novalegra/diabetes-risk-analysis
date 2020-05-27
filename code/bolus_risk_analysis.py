# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt

from pyod.models.knn import KNN
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta

# Offsets are in minutes
def find_bgs(time_string, before_offset, after_offset):
    date = pd.to_datetime(time_string)
    start = date - pd.Timedelta(minutes = before_offset)
    end = date + pd.Timedelta(minutes = after_offset)

    relevent_rows = list(
        bgs.loc[
            (bgs["time"] > start) 
            & (bgs["time"] < end)
        ].drop_duplicates(subset="value")["value"]
    )
    return relevent_rows


def return_first_matching_bg(time_string, before_offset, after_offset):
    result = find_bgs(time_string, before_offset, after_offset)

    return result[0] if len(result) > 0 else df["bgInput"].mean()


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

# Create a df with the data relevent to boluses
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
df = df.replace({"type": bolus_map})
df.fillna({"carbInput": 0, "normal": 0, "extended": 0}, inplace=True)

# Filter to get boluses
df = df.loc[(df["type"] == 1),]
df["totalAmount"] = df["normal"] + df["extended"]
# Drop if any values are NaN
df.dropna(subset=["totalAmount", "insulinCarbRatio", "insulinSensitivity"], inplace=True)
# Fill BG input columns
df["bgInput"].fillna(
    df["time"].apply(return_first_matching_bg, args=(5, 5)), 
    inplace=True
)

# Print some summary statistics
print("Head")
print(df.head(), "\n")
shape = df.shape
print("Shape", shape)
print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

# will want to play around with n_neighbors
model = KNN()
model.fit(df[["totalAmount", "carbInput", "insulinCarbRatio", "bgInput", "insulinSensitivity"]])

predictions = model.predict(df[["totalAmount", "carbInput", "insulinCarbRatio", "bgInput", "insulinSensitivity"]])
df["abnormal"] = predictions
unique, counts = np.unique(predictions, return_counts=True)
print ("Outliers:", counts[1], "\nTotal:", shape[0], "\n Percent:", round(counts[1]/shape[0] * 100), "%")

# Plot the results
fig = plt.figure(1, figsize=(7,7))
ax = Axes3D(fig, rect=[0, 0, 0.95, 1], elev=48, azim=134)
ax.scatter(df["totalAmount"], df["carbInput"], df["insulinCarbRatio"],
        c=predictions, edgecolor="k", s=50)
ax.set_xlabel("Bolus Amount")
ax.set_ylabel("Carb Amount")
ax.set_zlabel("CR")

plt.title("KNN To Classify Boluses", fontsize=14)
plt.show()

# Select our abnormal rows
abnormals = df.query('abnormal == 1')
abnormals = abnormals.sort_values("time")
abnormals["bgs_before"] = abnormals["time"].apply(find_bgs, args=(120, 5))
abnormals["bgs_after"] = abnormals["time"].apply(find_bgs, args=(5, 120))

time = datetime.now().strftime("%H_%M_%S")
file_name = "abnormal_boluses_" + time
abnormals.to_csv(file_name + ".csv")