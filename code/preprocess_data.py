import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime
from utils import (
    find_TDD,
    find_values,
    annotate_with_sax,
    return_first_matching_bg,
    find_duration_of_gap,
)


def preprocess_dose_data(
    initial_df, bgs, sax_df, sax_interval=10, bg_consideration_interval=180
):
    doses = make_dose_df(initial_df)

    # Get total amounts & TDD
    doses.fillna(
        {
            "normal": 0,
            "extended": 0,
            "rate": 0,
            "carbInput": 0,
            "insulinCarbRatio": doses["insulinCarbRatio"].median(),
            "insulinSensitivity": doses["insulinSensitivity"].median(),
        },
        inplace=True,
    )
    doses["totalBolusAmount"] = doses["normal"] + doses["extended"]
    doses.fillna({"totalBolusAmount": 0}, inplace=True)
    print("Filled in preprocessing fields with map")

    tdd_dict = {}
    doses["TDD"] = doses["time"].apply(find_TDD, args=(doses, tdd_dict))
    print("Got TDD")

    # Get BG input for boluses
    doses["bgInput"].fillna(
        doses["time"].apply(return_first_matching_bg, args=(doses, bgs, -5, 5)),
        inplace=True,
    )
    print("Got BG input")

    # Get the SAX string representations
    doses["before_event_strings"] = doses["time"].apply(
        annotate_with_sax, args=(sax_df, sax_interval, -bg_consideration_interval)
    )
    print("Got SAX before")

    doses["after_event_strings"] = doses["time"].apply(
        annotate_with_sax, args=(sax_df, sax_interval, bg_consideration_interval)
    )

    print("Got SAX before")
    print(doses.head())

    return doses


""" Find 'bg_consideration_interval'-worth of the BGs before & after a df of dose events, in addition to the length of CGM data loss """


def find_bgs_before_and_after(initial_df, bgs, bg_consideration_interval=180):
    doses = make_dose_df(initial_df)
    # Get BGs before the event
    doses["bgs_before"] = doses["time"].apply(
        find_values, args=(bgs, -bg_consideration_interval, 5, "value")
    )
    doses["duration_gaps_before"] = doses["bgs_before"].apply(find_duration_of_gap)
    doses["bg_30_min_before"] = doses["time"].apply(
        return_first_matching_bg, args=(doses, bgs, -31, -24)
    )
    print("Got BGs before")

    # Get BGs after the event
    doses["bgs_after"] = doses["time"].apply(
        find_values, args=(bgs, -5, bg_consideration_interval, "value")
    )
    doses["duration_gaps_after"] = doses["bgs_after"].apply(find_duration_of_gap)
    # 75 mins because of insulin peak
    doses["bg_75_min_after"] = doses["time"].apply(
        return_first_matching_bg, args=(doses, bgs, 74, 79)
    )
    print("Got BGs after")

    return doses


def make_dose_df(initial_df):
    # This column is commonly missing
    if not "extended" in initial_df:
        initial_df["extended"] = 0
    if not "percent" in initial_df:
        initial_df["percent"] = None

    # Create a df with dosing information
    try:
        doses = initial_df[
            [
                # Categorical
                "jsonRowIndex",
                "type",  # type of data: CBG, basal, bolus, etc
                "time",
                "subType",  # subtype of bolus: normal, extended, dual wave
                "deliveryType",  # type of basal: scheduled (according to programmed basal schedule) vs temp
                # Numerical
                "normal",  # units delivered via a "normal" bolus
                "extended",  # units delivered via an extended bolus
                "rate",  # absolute basal rate
                "insulinCarbRatio",
                "carbInput",  # number of carbs input into bolus calculator
                "insulinOnBoard",
                "bgInput",
                "insulinSensitivity",
                "duration",  # temp basal length
                "percent",  # percent of basal rate
            ]
        ]
    except KeyError as e:
        raise KeyError("Missing data column in the input data file; " + str(e))

    dose_map = {"basal": 0, "bolus": 1}
    doses = doses.replace({"type": dose_map})
    # Filter to get doses
    doses = doses.loc[(doses["type"] == 0) | (doses["type"] == 1)]
    # Make times into pandas datetimes
    doses["time"] = pd.to_datetime(doses["time"], infer_datetime_format=True)
    return doses.sort_values("time")
