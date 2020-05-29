import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime
from utils import find_TDD, find_values, annotate_with_sax, return_first_matching_bg

path = None
while path == None or len(path) < 5:
    path = input("Path to input file: ")

sax_input_path = str(Path(__file__).parent.parent) + "/results/ten_min_avg.csv"
sax_interval = 10
bg_consideration_interval = 180

try:
    export_path = input("Output file path (default: current folder): ")
except:
    export_path = ""

# Read in data
initial_df = pd.read_csv(path)

# Get SAX df
sax_df = pd.read_csv(sax_input_path)
sax_df["time"] = pd.to_datetime(sax_df["time"], infer_datetime_format=True)

# Create a dataframe with only the BG values
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

# Create a df with dosing information
doses = initial_df[
    [
        # Categorical
        "type", # type of data: CBG, basal, bolus, etc
        "time",
        "subType", # subtype of bolus: normal, extended, dual wave
        "deliveryType", # type of basal: scheduled (according to programmed basal schedule) vs temp

        # Numerical
        "normal", # units delivered via a "normal" bolus
        "extended", # units delivered via an extended bolus
        "rate", # absolute basal rate
        "insulinCarbRatio", 
        "carbInput", # number of carbs input into bolus calculator
        "insulinOnBoard",
        "bgInput",
        "insulinSensitivity",
        "duration", # temp basal length
        "percent", # percent of basal rate
    ]
]

dose_map = {"basal": 0, "bolus": 1}
doses = doses.replace({"type": dose_map})
# Filter to get doses
doses = doses.loc[(doses["type"] == 0) | (doses["type"] == 1)]
# Make times into pandas datetimes
doses["time"] = pd.to_datetime(doses["time"], infer_datetime_format=True)
doses = doses.sort_values("time")

# Get total amounts & TDD
doses.fillna(
    {"normal": 0, 
    "extended": 0, 
    "rate": 0, 
    "carbInput": 0, 
    "insulinCarbRatio": doses["insulinCarbRatio"].median(), 
    "insulinSensitivity": doses["insulinSensitivity"].median()
    }, inplace=True
)
doses["totalBolusAmount"] = doses["normal"] + doses["extended"]
doses.fillna({"totalBolusAmount": 0}, inplace=True)
doses["TDD"] = doses["time"].apply(find_TDD, args=(doses, 0))

# Get BGs before/after the event
doses["bgs_before"] = doses["time"].apply(find_values, args=(bgs, bg_consideration_interval, 5, "value"))
doses["bgs_after"] = doses["time"].apply(find_values, args=(bgs, 5, bg_consideration_interval, "value"))

# Get BG input for boluses
doses["bgInput"].fillna(
    doses["time"].apply(return_first_matching_bg, args=(doses, bgs, 5, 5)), 
    inplace=True
)

# Get the SAX string representations
doses["before_event_strings"] = doses["time"].apply(
    annotate_with_sax, 
    args=(sax_df, sax_interval, -bg_consideration_interval)
)

doses["after_event_strings"] = doses["time"].apply(
    annotate_with_sax, 
    args=(sax_df, sax_interval, bg_consideration_interval)
)

print(doses.head())

# Convert dose type numbers back to strings for readibility
dose_string_map = {0: "basal", 1: "bolus"}
doses = doses.replace({"type": dose_map})

time = datetime.now().strftime("%H_%M_%S")
file_name = "processed_dose_events_" + time
doses.to_csv(export_path + file_name + ".csv")
print("Successfully exported!")
