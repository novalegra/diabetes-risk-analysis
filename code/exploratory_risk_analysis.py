# Tidepool data model: https://developer.tidepool.org/data-model/

import numpy as np
import pandas as pd
import matplotlib.pylab as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from pathlib import Path

# Load in data
path = str(Path(__file__).parent.parent)
initial_df = pd.read_csv(path + "/data/risk-data-sample.csv")

df = initial_df[
    [
        # Categorical
        #"time", 
        "type", # type of data: CBG, basal, bolus, etc
        "est.localTime", # local time
        "deliveryType", # scheduled vs temp basal
        "deviceTime", # time on the device
        "units", # units of BG measurement

        # Numerical
        "expectedDuration", # duration of scheduled and/or temp basal?
        "percent", # percent of basal rate
        "rate", # absolute basal rate
        "insulinOnBoard", # IOB
        "recommended.net", # recommended bolus?
        "carbInput", # input carb value (g)
        "value" # BG value
    ]
]

# Fill NaN values
#df = df.dropna(subset=["type", "est.localTime"])
'''df.fillna(
    {
        "type":"none",
        "deliveryType":"n/a",
        "units":df["units"].mode(),
        
        "expectedDuration":0,
        "percent":100,
        "rate":df["rate"].median(), # TODO: check in about this one
        "insulinOnBoard":df["insulinOnBoard"].median(), # TODO: check in about this one
        "recommended.net":0,
        "carbInput":0,
        #"value":df["value"].median(), # TODO: check in about this one
    },
    inplace=True
)'''

# Print some summary statistics
print("Head")
print(df.head(), "\n")
print("Shape", df.shape)
print(df.nunique(axis=0))
print(df.describe().apply(lambda s: s.apply(lambda x: format(x, "f"))))

print(df["type"].value_counts())
# Get a sense of distribution
#sns.distplot(df["expectedDuration"])
#sns.despine()
#plt.scatter(range(df.shape[0]), np.sort(df["percent"].values))
plt.show()


# Print correlation plot
'''
corr = df.corr(min_periods=10) # Plot the heatmap
print(corr.columns)
sns.heatmap(corr, xticklabels=corr.columns, yticklabels=corr.columns, annot=True, cmap=sns.diverging_palette(220, 20, as_cmap=True))
plt.show()
'''

'''
# Create isolation forest for one attribute
df.dropna(subset=["expectedDuration"], inplace=True)
isolation_forest = IsolationForest(n_estimators=100)
isolation_forest.fit(df["expectedDuration"].values.reshape(-1, 1))
xx = np.linspace(df["expectedDuration"].min(), df["expectedDuration"].max(), len(df)).reshape(-1,1)
anomaly_score = isolation_forest.decision_function(xx)
outlier = isolation_forest.predict(xx)
plt.figure(figsize=(10,4))
plt.plot(xx, anomaly_score, label='anomaly score')
plt.fill_between(xx.T[0], np.min(anomaly_score), np.max(anomaly_score), 
                 where=outlier==-1, color='r', 
                 alpha=.4, label='outlier region')
plt.legend()
plt.ylabel('Anomaly Score')
plt.xlabel('Expected Duration')
plt.show()
'''