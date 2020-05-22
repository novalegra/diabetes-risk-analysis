#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from sklearn import datasets
import pandas as pd

# Diabetes Dataset
diabetes = datasets.load_diabetes()
df = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
df["score"] = diabetes.target
x = df[["bmi", "s1", "bp"]]
X = diabetes.data
# Generate KMeans
km = KMeans(n_clusters=2)
km.fit(x)
km.predict(x)
labels = km.labels_

# Plotting
fig = plt.figure(1, figsize=(7,7))
ax = Axes3D(fig, rect=[0, 0, 0.95, 1], elev=48, azim=134)
ax.scatter(X[:, 3], X[:, 0], X[:, 2],
          c=labels.astype(np.float), edgecolor="k", s=50)
ax.set_xlabel("BMI")
ax.set_ylabel("Blood glucose reading")
ax.set_zlabel("Blood pressure")
plt.title("K Means", fontsize=14)
plt.show()

