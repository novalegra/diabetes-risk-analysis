# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt

from pyod.models.knn import KNN
from sklearn.ensemble import IsolationForest

from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta
from utils import extract_array


def find_abnormal_boluses(processed_df, bgs, model_type="knn"):
    df = extract_and_process_boluses(processed_df)

    # Print some summary statistics
    print("Head")
    print(df.head(), "\n")
    shape = df.shape
    print("Shape", shape)
    print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

    data_to_predict = df[
        [
            "totalBolusAmount",
            "carbInput",
            "insulinCarbRatio",
            "bgInput",
            "insulinSensitivity",
            "TDD",
            "bg_30_min_before",
            "bg_75_min_after",
        ]
    ]
    model = train_model(data_to_predict, model_type)
    predictions = model.predict(data_to_predict)
    df["abnormal"] = predictions
    if model_type == "isolation_forest":
        df["abnormality_score"] = model.decision_function(data_to_predict)

    # Plot the results
    # Note that this plot only incorporates 3 dimensions of the data, so there are other
    # factors present that might explain why certain values were/were not classified as outliers
    """
    fig = plt.figure(1, figsize=(7,7))
    ax = Axes3D(fig, rect=[0, 0, 0.95, 1], elev=48, azim=134)
    ax.scatter(df["totalBolusAmount"], df["carbInput"], df["TDD"],
            c=df["abnormal], edgecolor="k", s=50)
    ax.set_xlabel("Bolus Amount")
    ax.set_ylabel("Carb Amount")
    ax.set_zlabel("TDD")

    plt.title("IF To Classify Boluses" if model_type == "isolation_forest" else "KNN To Classify Boluses", fontsize=14)
    plt.show()
    """
    # Filter for only doses with BG value post-event that's below 1st inter-quartile range, excluding missing values
    lower_bg_bound = max(70 / 18, bgs["value"].quantile(0.25))
    print("BG at 25th-percentile IQRL", lower_bg_bound)
    df["bgs_after"] = df["bgs_after"].apply(extract_array)
    df = df[df["bgs_after"].apply(lambda l: any(2 < bg <= lower_bg_bound for bg in l))]
    unique, counts = np.unique(df["abnormal"], return_counts=True)

    # Select our abnormal rows
    # Isolation forest: 1 is normal, -1 is abnormal
    # KNN: 0 is normal, 1 is abnormal
    abnormals = (
        df.query("abnormal == -1")
        if model_type == "isolation_forest"
        else df.query("abnormal == 1")
    )

    if (
        len(counts) > 1
    ):  # Check to make sure there are both outliers & normal values (not just 1 type)
        if model_type == "isolation_forest":
            print(
                "Outliers:",
                counts[0],
                "\nTotal:",
                shape[0],
                "\nPercent:",
                round(counts[0] / shape[0] * 100),
                "%",
            )
        else:
            print(
                "Outliers:",
                counts[1],
                "\nTotal:",
                shape[0],
                "\nPercent:",
                round(counts[1] / shape[0] * 100),
                "%",
            )

    return abnormals


def train_model(data_to_predict, model_type):
    """ Train the specified model type (either knn or isolation_forest) and return the trained model """
    if model_type == "isolation_forest":
        # Set a random state for reproducable results
        rng = np.random.RandomState(42)
        model = IsolationForest(random_state=rng, contamination=0.05)
    # will want to play around with parameter tuning once dataset is labeled
    else:
        model = KNN()

    model.fit(data_to_predict)

    return model


def extract_and_process_boluses(processed_df):
    """ Take a dataframe of processed dose values and extract/further process the boluses from it """
    # Create a df with the data relevent to boluses
    df = processed_df[
        [
            # Categorical
            "jsonRowIndex",
            "type",  # type of data: CBG, basal, bolus, etc
            "time",
            # "subType" # subtype of bolus: normal, extended, dual wave
            # Numerical
            "normal",  # units delivered via a "normal" bolus
            "extended",  # units delivered via an extended bolus
            "insulinCarbRatio",
            "carbInput",  # number of carbs input into bolus calculator
            "insulinOnBoard",
            "bgInput",
            "insulinSensitivity",
            "duration_gaps_before",
            "duration_gaps_after",
            # Fields from processing
            "totalBolusAmount",
            "TDD",
            "bgs_before",
            "bgs_after",
            "before_event_strings",
            "after_event_strings",
            "bg_30_min_before",
            "bg_75_min_after",
        ]
    ]

    # Filter to get boluses
    df = df.loc[
        (df["type"] == 1),
    ]
    # Drop if any values are NaN
    df.dropna(
        subset=[
            "totalBolusAmount",
            "insulinCarbRatio",
            "insulinSensitivity",
            "TDD",
            "bg_30_min_before",
            "bg_75_min_after",
        ],
        inplace=True,
    )
    # Convert the time strings to pandas datetime format
    df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True)

    return df
