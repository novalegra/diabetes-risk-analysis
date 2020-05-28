import numpy as np
import pandas as pd

# Offsets are in minutes
def find_bgs(time_string, bgs, before_offset, after_offset):
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

# Get the first matching BG within the time interval
def return_first_matching_bg(time_string, df, bgs, before_offset, after_offset):
    result = find_bgs(time_string, bgs, before_offset, after_offset)

    return result[0] if len(result) > 0 else df["bgInput"].mean()

# TODO: may want to convert the string to time beforehand, this assumes the sax_df is time-coverted
def annotate_with_sax(time_string, sax_df, sax_interval_length, time_length_of_string):
    date = pd.to_datetime(time_string)
    rounding_string = str(sax_interval_length) + "min"

    start = (
        date + pd.Timedelta(minutes = time_length_of_string)
        ).round(rounding_string) if time_length_of_string < 0 else date
    end = (
        date + pd.Timedelta(minutes = time_length_of_string)
        ).round(rounding_string) if time_length_of_string > 0 else date

    string = "".join (
        list(
            sax_df.loc[
                (sax_df["time"] >= start) 
                & (sax_df["time"] <= end)
            ]["bin"]
        )
    )

    return string