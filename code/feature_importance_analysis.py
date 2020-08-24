import shap
import numpy as np
import pandas as pd
import matplotlib.pylab as plt

from sklearn.ensemble import IsolationForest
from os.path import exists

from bolus_risk_analysis import extract_and_process_boluses, train_model
from basal_risk_analysis import extract_and_process_temp_basals


# Path to the file of processed doses - YOU MUST FILL THIS IN
path_to_file = "TO_FILL_IN.csv"
assert exists(path_to_file)
# YOU MUST CHANGE THIS TO CHANGE THE DOSE TYPE THAT IS ANALYZED
dose_type = "boluses"  # either "basals" or "boluses"

if dose_type == "boluses":
    df = extract_and_process_boluses(pd.read_csv(path_to_file))
    # Get trained model
    data_to_predict = df[
        [
            "totalBolusAmount",
            "carbInput",
            "insulinCarbRatio",
            "bgInput",
            "insulinSensitivity",
            "TDD",
            "bg_30_min_before",
            "bg_75_min_after",
        ]
    ]
elif dose_type == "basals":
    df = extract_and_process_temp_basals(pd.read_csv(path_to_file))
    data_to_predict = df[
        [
            "duration",
            "percent",
            "rate",
            "bgInput",
            "bg_30_min_before",
            "bg_75_min_after",
        ]
    ]
else:
    ValueError("Invalid dose type selected")

trained_model = train_model(data_to_predict, "isolation_forest")
# Explain the model's predictions using SHAP
explainer = shap.TreeExplainer(trained_model)
shap_values = explainer.shap_values(data_to_predict)

# Plot the variables, ranked by impact on abnormality score
shap.summary_plot(shap_values, data_to_predict, plot_type="bar")

# For each data feature, plot the impact on abnormality score vs value (negative -> more abnormal)
for col in data_to_predict.columns:
    shap.dependence_plot(col, shap_values, data_to_predict)
