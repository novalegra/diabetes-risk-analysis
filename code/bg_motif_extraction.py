import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from collections import deque
from tslearn.clustering import TimeSeriesKMeans

# Load data
path = str(Path(__file__).parent.parent)
bgs = pd.read_csv(path + "/data/random_person_processed_bgs.csv")
seed = 0

# interval length is in mins
def bin_into_intervals(bgs, interval_length, delta=5):
    intervals_per_window = round(interval_length / delta)
    bg_list = bgs["value"].tolist()
    bg_list = [i * 18 for i in bg_list]

    if len(bg_list) < intervals_per_window:
        Exception("Cannot form", interval_length, "minute windows with", len(bg_list) * delta, "minutes of data")
    output_builder = []
    curr = deque(bg_list[0:interval_length]) # initialize with interval_length BGs

    for i in range(interval_length, len(bgs)):
        output_builder.append(list(curr))
        curr.popleft()
        curr.append(bg_list[i])

    return np.matrix(output_builder)

x = bin_into_intervals(bgs, 60)
km = TimeSeriesKMeans(n_clusters=20, verbose=True, random_state=seed)
y_pred = km.fit_predict(x)

np.savetxt("motif_output.csv", y_pred, delimiter=",")

sz = x.shape[1]
plt.figure()
for yi in range(20):
    plt.subplot(4, 5, yi + 1)
    i = 0
    for xx in x[y_pred == yi]:
        if i > 5: continue
        plt.plot(xx.ravel(), "k-", alpha=.2)
        i += 1
    plt.plot(km.cluster_centers_[yi].ravel(), "r-")
    plt.xlim(0, sz)
    plt.text(0.55, 0.85,'Cluster %d' % (yi + 1),
             transform=plt.gca().transAxes)
    if yi == 1:
        plt.title("Euclidean $k$-means")
plt.show()