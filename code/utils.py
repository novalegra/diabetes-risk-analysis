import os
import numpy as np
import pandas as pd
from pathlib import Path


def extract_array(s):
    """
    Take an "exported" array string from Excel and make it into an actual array

    s: string of array to convert
    """
    return (
        [float("".join([c for c in i if c in "1234567890.-"])) for i in s.split(",")]
        if len(s) > 2
        else []
    )


def find_values(date, df, first_offset, second_offset, key):
    """ 
    Get all of the values within the time interval

    date: Pandas datetime w/date of event
    df: dataframe with the data, must contain "time" column with Pandas datetimes and whatever the 'key' column is
    first_offset: offset to apply to the beginning of the range, in minutes (can be negative)
    second_offset: offset to apply to the end of the range, in minutes (can be negative)

    Returns: a list of the values
    """
    start = date + pd.Timedelta(minutes=first_offset)
    end = date + pd.Timedelta(minutes=second_offset)

    relevent_rows = list(
        df.loc[(df["time"] > start) & (df["time"] < end)].drop_duplicates(
            subset="time"
        )[key]
    )
    return relevent_rows


def return_first_matching_bg(date, df, bgs, first_offset, second_offset):
    """ 
    Get the first matching BG within the time interval

    date: Pandas datetime w/date of event
    df: dataframe with the bolus dosing data, must contain "bgInput" column
    bgs: dataframe with the BG data, must contain "time" column with Pandas datetimes
    first_offset: offset to apply to the beginning of the range, in minutes (can be negative)
    second_offset: offset to apply to the end of the range, in minutes (can be negative)

    Returns: the first matching BG, if it can be found, and otherwise the average bgInput
    """
    result = find_values(date, bgs, first_offset, second_offset, "value")

    return result[0] if len(result) > 0 else df["bgInput"].mean()


def annotate_with_sax(date, sax_df, sax_interval_length, time_length_of_string):
    """
    Get the SAX representation of a time series from a df with the SAX encodings

    date: Pandas datetime w/date of event
    sax_df: dataframe containing SAX representations for the BG time series
    sax_interval_length: length of time of the SAX interval in minutes
    time_length_of_string: desired length of the string,
                        can be negative to get values from before the event

    returns the SAX string
    """
    rounding_string = str(sax_interval_length) + "min"

    start = (
        (date + pd.Timedelta(minutes=time_length_of_string)).round(rounding_string)
        if time_length_of_string < 0
        else date.round(rounding_string)
    )
    end = (
        (date + pd.Timedelta(minutes=time_length_of_string)).round(rounding_string)
        if time_length_of_string > 0
        else date.round(rounding_string)
    )

    if time_length_of_string < 0:
        string = "".join(
            list(sax_df.loc[(sax_df["time"] >= start) & (sax_df["time"] < end)]["bin"])
        )
    else:
        string = "".join(
            list(sax_df.loc[(sax_df["time"] > start) & (sax_df["time"] <= end)]["bin"])
        )

    return string


def find_TDD(date, df, tdd_dict):
    """
    Finds the total daily dose (TDD) of insulin for a given day.
    
    date: date to compute the TDD on
    df: dataframe containing dosing data, which must have "totalBolusAmount" and "rate" columns
    tdd_dict: dict to cache results for performance improvements

    Returns: total insulin given over a 24 hour period
    """
    midnight = pd.DatetimeIndex([date]).normalize()[0]
    if midnight in tdd_dict:
        return tdd_dict[midnight]

    mins_in_day = 24 * 60

    boluses = find_values(midnight, df, 0, mins_in_day + 1, "totalBolusAmount")
    basals = find_values(midnight, df, 0, mins_in_day + 1, "rate")
    tdd = sum(boluses) + sum(basals)
    tdd_dict[midnight] = tdd

    return tdd


def get_column_TDDs(df):
    return df["time"].apply(find_TDD, args=(df))


def read_bgs_from_df(df, bg_timedelta=5):
    """
    Take a dataframe with a variety of data and extract the BG values.
    
    df - dataframe with initial data
       - required columns: 
            - "type" (where BG values are 'cbg')
            - "time" (string of the date/time)
            - "value" (the BG value, likely in mmol/L)
    bg_timedelta - minutes between each BG value
    
    Returns: df with "type", "time", "value", and "logBG" columns,
      where the time column has a consistant interval of bg_timedelta
      minutes, all missing BG values are filled with -1
    """
    bgs = df[
        [
            # Categorical
            "type",  # type of data: CBG, basal, bolus, etc
            "time",
            # Numerical
            "value",  # BG reading in mmol/L
        ]
    ]
    # Filter out other dose types
    bg_map = {"cbg": 2}
    bgs = bgs.replace({"type": bg_map})
    bgs = bgs.loc[(bgs["type"] == 2)]

    # Get time
    bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)

    # Make time intervals standardized
    interval_string = str(bg_timedelta) + "min"
    standardized_times = bgs.groupby(
        pd.Grouper(key="time", freq=interval_string)
    ).mean()
    bgs = bgs.set_index(["time"]).resample("5min").last().reset_index()

    # Take log of BG values
    bgs["log_bg"] = np.log10(bgs["value"])
    # Fill in missing BG values
    bgs["value"].fillna(-1, inplace=True)

    return bgs


def find_duration_of_gap(
    bg_list, missing_data_key=-1, time_interval=5, list_duration=180
):
    """
        Finds the number of minutes of missing BG data over a given interval

        bg_list: list of BG values
        missing_data_key: the value given to missing values
        time_interval: minutes between each BG value
        list_duration: expected number of minutes of data in each list

        Returns: number of minutes where no BG data is present
    """
    return bg_list.count(missing_data_key) * 5 + max(0, (180 / 5 - len(bg_list)) * 5)


def find_full_path(resource_name, extension):
    """ Find file path, given name and extension
        example: "/home/pi/Media/tidepool_demo.json"

        This will return the *first* instance of the file

    Arguments:
    resource_name -- name of file without the extension
    extension -- ending of file (ex: ".json")

    Output:
    path to file
    """
    search_dir = Path(__file__).parent.parent
    print(search_dir)
    for root, dirs, files in os.walk(search_dir):  # pylint: disable=W0612
        for name in files:
            (base, ext) = os.path.splitext(name)
            if base == resource_name and extension == ext:
                return os.path.join(root, name)

    raise Exception("No file found for specified resource name & extension")
