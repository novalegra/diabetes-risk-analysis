import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime
from utils import find_TDD, find_values, annotate_with_sax, return_first_matching_bg


def preprocess_dose_data(initial_df, bgs, sax_df, sax_interval=10, bg_consideration_interval=180):
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
    print("Filled in preprocessing fields with map")
    doses["TDD"] = doses["time"].apply(find_TDD, args=(doses, 0))
    print("Got TDD")

    # Get BGs before/after the event
    doses["bgs_before"] = doses["time"].apply(find_values, args=(bgs, bg_consideration_interval, 5, "value"))
    print("Got BGs before")
    doses["bgs_after"] = doses["time"].apply(find_values, args=(bgs, 5, bg_consideration_interval, "value"))
    print("Got BGs after")

    # Get BG input for boluses
    doses["bgInput"].fillna(
        doses["time"].apply(return_first_matching_bg, args=(doses, bgs, 5, 5)), 
        inplace=True
    )
    print("Got BG input")

    # Get the SAX string representations
    doses["before_event_strings"] = doses["time"].apply(
        annotate_with_sax, 
        args=(sax_df, sax_interval, -bg_consideration_interval)
    )
    print("Got SAX before")

    doses["after_event_strings"] = doses["time"].apply(
        annotate_with_sax, 
        args=(sax_df, sax_interval, bg_consideration_interval)
    )

    print("Got SAX before")
    print(doses.head())

    return doses