# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt

from pyod.models.knn import KNN
from sklearn.ensemble import IsolationForest

from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime
from bolus_risk_analysis import train_model

def find_abnormal_temp_basals(processed_df, bgs, model_type="knn"):
    print(processed_df.head())
    df = extract_and_process_temp_basals(processed_df)

    # Print some summary statistics
    print("Head")
    print(df.head(), "\n")
    shape = df.shape
    print("Shape", shape)
    print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

    data_to_predict = df[
        [
            "duration", 
            "percent", 
            "rate",
            "bgInput",
            "bg_30_min_before", 
            "bg_75_min_after"
        ]
    ]
    
    model = train_model(data_to_predict, model_type)
    predictions = model.predict(data_to_predict)
    df["abnormal"] = predictions
    if model_type == "isolation_forest":
        df["abnormality_score"] = model.decision_function(data_to_predict)
    unique, counts = np.unique(predictions, return_counts=True)

    # Plot the results
    # Note that this plot only incorporates 3 dimensions of the data, so there are other 
    # factors present that might explain why certain values were/were not classified as outliers
    
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
    if model_type == "isolation_forest":
        # Isolation forest: 1 is normal, -1 is abnormal
        if len(counts) > 1: # Check to make sure there are both outliers & normal values (not just 1 type)
            print ("Outliers:", counts[0], "\nTotal:", shape[0], "\nPercent:", round(counts[0]/shape[0] * 100), "%")
        abnormals = df.query('abnormal == -1')
    else:
        # KNN: 0 is normal, 1 is abnormal
        if len(counts) > 1: # Check to make sure there are both outliers & normal values (not just 1 type)
            print ("Outliers:", counts[1], "\nTotal:", shape[0], "\nPercent:", round(counts[1]/shape[0] * 100), "%")
        abnormals = df.query('abnormal == 1')

    return abnormals

''' Take a dataframe of processed dose values and extract/further process the *temp* basals from it '''
def extract_and_process_temp_basals(processed_df):
    # Create a df with the data relevent to basals
    df = processed_df[
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
            "bgInput",
            "bg_30_min_before", 
            "bg_75_min_after"
        ]
    ]
    type_map = {"temp": 0}

    df = df.replace({"deliveryType": type_map})
    # Filter to get temp basals
    df = df.loc[(df["type"] == 0) & (df["deliveryType"] == 0)]
    # Drop if any of the values that would be passed into model are NaN
    df.dropna(subset=[
        "duration", 
        "percent", 
        "rate",
        "bgInput",
        "bg_30_min_before", 
        "bg_75_min_after"
    ], inplace=True)
    # Convert the time strings to pandas datetime format
    df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True)

    return df