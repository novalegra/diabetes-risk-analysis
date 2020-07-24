import matplotlib.pyplot as plt
import pandas as pd


def plot_bg_frequencies(bg_df):
    df = bg_df.groupby("log_bg").count()
    # Include the line below if you want to exclude signal loss values from the plot
    df = df.iloc[1:]

    # Convert mmol -> mg/dL
    values = [18 * x for x in list(df.index)]

    plt.scatter(values, df["time"])
    plt.title("BG Distribution")
    plt.xlabel("Log BG (mg/dL)")
    plt.ylabel("Count of Occurances")
    plt.show()
