from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from math import isnan

# Load in data
path = str(Path(__file__).parent.parent)
file_name = input("File name: ")
df = pd.read_csv(path + "/data/" + file_name + ".csv")

while True:
    file_index = int(input("What row number would you like visualized? (indexed including the csv header) ")) - 2
    # Get times & values
    ''' 
    NOTE: this makes the assumption that the 'before' and 'after' values 
    are continous, and that the interval between measurements is 5 minutes, 
    which may lead to faulty predictions in the event of missing CGM data
    '''
    before_event_values = [
        float(
            ''.join(
                [c for c in i if c in '1234567890.']
                )
        ) for i in df["bgs_before"].iloc[file_index].split(",")
    ] if len(df["bgs_before"].iloc[file_index]) > 2 else []

    after_event_values = [
            float(
                ''.join(
                    [c for c in i if c in '1234567890.']
                    )
            ) for i in df["bgs_after"].iloc[file_index].split(",")
        ] if len(df["bgs_after"].iloc[file_index]) > 2 else []

    event_bg = (
        df["bgInput"].iloc[file_index] if not isnan(df["bgInput"].iloc[file_index])
        else (before_event_values[-1] + after_event_values[0]) / 2
    )

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
    plt.ylim(40, 300)
    plt.scatter(all_times, all_bg_values)
    # Plot the BG at the abnormal event as a star
    plt.scatter([0], [event_bg], marker="o", s=100)
    plt.title(
        "Row " + str(file_index + 2) 
        + ", carb-based residual = "
        + str(
            round(
                df["totalAmount"].iloc[file_index] 
                - df["carbInput"].iloc[file_index] / df["insulinCarbRatio"].iloc[file_index], 2)
            )
        )
    plt.savefig("bg_graph_for_row_" + str(file_index + 2) + ".png")
    plt.show()