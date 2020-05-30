import pandas as pd

from pathlib import Path

from utils import read_bgs_from_df
from bg_sax_analysis import get_sax_encodings
from preprocess_data import preprocess_dose_data
from bolus_risk_analysis import find_abnormal_boluses
from basal_risk_analysis import find_abnormal_temp_basals

path = str(Path(__file__).parent.parent) + "/data/random_person.csv"
export_path = str(Path(__file__).parent.parent) + "/results/"

initial_df = pd.read_csv(path)
bgs = read_bgs_from_df(initial_df)
bgs.to_csv(export_path + "bgs" + ".csv")
print("Loaded BGs")

sax_encodings = get_sax_encodings(bgs)
sax_encodings.to_csv(export_path + "sax" + ".csv")
print("Loaded SAX")

processed_doses = preprocess_dose_data(initial_df, bgs, sax_encodings)
processed_doses.to_csv(export_path + "processed_doses" + ".csv")

abnormal_boluses = find_abnormal_boluses(processed_doses)
abnormal_boluses.to_csv(export_path + "abnormal_boluses" + ".csv")