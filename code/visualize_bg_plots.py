from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from math import isnan
from os.path import exists
from utils import extract_array

# Get user inputs
path = None
while path == None or not exists(path):
    path = input("Path to input file: ")
    if not exists(path):
        print("Path does not exist in computer, try again.")

# Load the data in
df = pd.read_csv(path)

# Get index to examine
file_index = -1
while file_index < 2 or file_index > len(df) + 1:
    try:
        file_index = int(
            input(
                "What row number would you like visualized? (indexed including the csv"
                " header) "
            )
        )
    except:
        print("Invalid entry; row must be between 2 and the size of the dataframe")
        continue
# convert to zero-indexed location
file_index -= 2

while True:
    # Get times & values
    before_event_values = extract_array(df["bgs_before"].iloc[file_index])
    after_event_values = extract_array(df["bgs_after"].iloc[file_index])

    if not isnan(df["bgInput"].iloc[file_index]):
        event_bg = df["bgInput"].iloc[file_index]
    elif (
        len(before_event_values) > 0
        and len(after_event_values) > 0
        and before_event_values[-1] != -1
        and after_event_values[0] != -1
    ):
        event_bg = (before_event_values[-1] + after_event_values[0]) / 2
    else:
        event_bg = 0

    relative_before_times = [5 * i for i in range(-1 + -len(before_event_values), -1)]
    relative_after_times = [5 * i for i in range(1, len(after_event_values) + 1)]

    all_times = []
    all_times.extend(relative_before_times)
    all_times.extend(relative_after_times)

    all_bg_values = []
    all_bg_values.extend(before_event_values)
    all_bg_values.extend(after_event_values)
    # Convert to mg/dL
    all_bg_values = [round(val * 18.0182, 3) for val in all_bg_values]
    event_bg *= 18.0182

    # Print out the data for the measurement
    print(df.iloc[file_index])

    # Plot the graph
    max_y = max(250, max(all_bg_values) + 10)
    min_y = 30
    plt.ylim(min_y, max_y)
    plt.scatter(all_times, all_bg_values)
    # Plot the BG at the abnormal event as a star
    plt.scatter([0], [event_bg], marker="o", s=100)
    plt.title("Dose at Row " + str(file_index + 2))
    plt.xlabel("Minutes since dose event")
    plt.ylabel("BG (mg/dL)")

    plt.show()

    try:
        file_index = (
            int(
                input(
                    "What row number would you like visualized? (indexed including the"
                    " csv header) "
                )
            )
            - 2
        )
        assert file_index >= 0 and file_index < len(df) + 1
    except:
        print("Quitting...")
        break
