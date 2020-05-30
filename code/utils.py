import numpy as np
import pandas as pd

""" 
Get all of the values within the time interval

date - Pandas datetime w/date of event
df - dataframe with the data, must contain "time" column with Pandas datetimes and whatever the 'key' column is
before_offset - offset to search before the event date, in minutes
after_offset - offset to search after the event date, in minutes

Returns a list of the values
"""
def find_values(date, df, before_offset, after_offset, key):
    start = date - pd.Timedelta(minutes = before_offset)
    end = date + pd.Timedelta(minutes = after_offset)

    relevent_rows = list(
        df.loc[
            (df["time"] > start) 
            & (df["time"] < end)
        ].drop_duplicates(subset="time")[key]
    )
    return relevent_rows

""" 
Get the first matching BG within the time interval

date - Pandas datetime w/date of event
df - dataframe with the bolus dosing data, must contain "bgInput" column
bgs - dataframe with the BG data, must contain "time" column with Pandas datetimes
before_offset - offset to search before the event date, in minutes
after_offset - offset to search after the event date, in minutes

Returns the first matching BG, if it can be found, and otherwise the average bgInput
"""
def return_first_matching_bg(date, df, bgs, before_offset, after_offset):
    result = find_values(date, bgs, before_offset, after_offset, "value")

    return result[0] if len(result) > 0 else df["bgInput"].mean()


"""
Get the SAX representation of a time series from a df with the SAX encodings

date - Pandas datetime w/date of event
sax_df - dataframe containing SAX representations for the BG time series
sax_interval_length - length of time of the SAX interval in minutes
time_length_of_string - desired length of the string,
                        can be negative to get values from before the event

returns the SAX string
"""
def annotate_with_sax(date, sax_df, sax_interval_length, time_length_of_string):
    rounding_string = str(sax_interval_length) + "min"

    start = (
        date + pd.Timedelta(minutes = time_length_of_string)
        ).round(rounding_string) if time_length_of_string < 0 else date.round(rounding_string)
    end = (
        date + pd.Timedelta(minutes = time_length_of_string)
        ).round(rounding_string) if time_length_of_string > 0 else date.round(rounding_string)

    if time_length_of_string < 0:
        string = "".join (
            list(
                sax_df.loc[
                    (sax_df["time"] >= start) 
                    & (sax_df["time"] < end)
                ]["bin"]
            )
        )
    else:
        string = "".join (
            list(
                sax_df.loc[
                    (sax_df["time"] > start) 
                    & (sax_df["time"] <= end)
                ]["bin"]
            )
        )

    return string

"""
df - dataframe containing dosing data

TODO: this could be more efficent if we used numpy arrays? also we're computing the TDD too many times
"""
def find_TDD(date, df, dummy_val):
    midnight = pd.DatetimeIndex([date]).normalize()[0]
    mins_in_day = 24 * 60

    boluses = find_values(midnight, df, 0, mins_in_day + 1, "totalBolusAmount")
    basals = find_values(midnight, df, 0, mins_in_day + 1, "rate")

    return sum(boluses) + sum(basals)


def get_column_TDDs(df):
    return df["time"].apply(find_TDD, args=(df))

"""
    Take a dataframe with a variety of data and extract the BG values
"""
def read_bgs_from_df(df):
    bgs = df[
        [
            # Categorical
            "type", # type of data: CBG, basal, bolus, etc
            "time",

            # Numerical
            "value" # BG reading in mmol/L
        ]
    ]
    # Filter out other dose types
    bg_map = {"cbg": 2}
    bgs = bgs.replace({"type": bg_map})
    bgs = bgs.loc[(bgs["type"] == 2)]

    # Get time
    bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)
    standardized_times = bgs.groupby(pd.Grouper(key="time", freq="5min")).mean()

    # Make time intervals standardized
    bgs = bgs.set_index(["time"]).resample("5min").last().reset_index()

    # Take log of BG values
    bgs["log_bg"] = np.log10(bgs["value"])
    # Fill in missing BG values
    bgs["value"].fillna(-1, inplace=True)

    return bgs


def find_duration_of_gap(bg_list, missing_data_key = -1, time_interval = 5, list_duration = 180):
    return max(bg_list.count(missing_data_key) * 5 + (180 / 5 - len(bg_list)) * 5, 0)
