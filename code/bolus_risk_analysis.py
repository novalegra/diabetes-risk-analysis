# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt

from pyod.models.knn import KNN
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta

def find_abnormal_boluses(processed_df):
    # Create a df with the data relevent to boluses
    df = processed_df[
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
            "insulinSensitivity",

            # Fields from processing
            "totalBolusAmount",
            "TDD",
            "bgs_before",
            "bgs_after",
            "before_event_strings",
            "after_event_strings",
            "bgInput"
        ]
    ]

    # Filter to get boluses
    df = df.loc[(df["type"] == 1),]
    # Drop if any values are NaN
    df.dropna(subset=["totalBolusAmount", "insulinCarbRatio", "insulinSensitivity", "TDD"], inplace=True)
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
    model.fit(df[["totalBolusAmount", "carbInput", "insulinCarbRatio", "bgInput", "insulinSensitivity", "TDD"]])

    predictions = model.predict(df[["totalBolusAmount", "carbInput", "insulinCarbRatio", "bgInput", "insulinSensitivity", "TDD"]])
    df["abnormal"] = predictions
    unique, counts = np.unique(predictions, return_counts=True)
    print ("Outliers:", counts[1], "\nTotal:", shape[0], "\n Percent:", round(counts[1]/shape[0] * 100), "%")

    '''# Plot the results
    fig = plt.figure(1, figsize=(7,7))
    ax = Axes3D(fig, rect=[0, 0, 0.95, 1], elev=48, azim=134)
    ax.scatter(df["totalBolusAmount"], df["carbInput"], df["TDD"],
            c=predictions, edgecolor="k", s=50)
    ax.set_xlabel("Bolus Amount")
    ax.set_ylabel("Carb Amount")
    ax.set_zlabel("TDD")

    plt.title("KNN To Classify Boluses", fontsize=14)
    plt.show()'''

    # Select our abnormal rows
    abnormals = df.query('abnormal == 1')
    return abnormals