import d6tflow
import pandas as pd

from pathlib import Path

from utils import read_bgs_from_df
from bg_sax_analysis import get_sax_encodings
from preprocess_data import preprocess_dose_data
from bolus_risk_analysis import find_abnormal_boluses
from basal_risk_analysis import find_abnormal_temp_basals

'''
Task Flow:
1) Get initial df
2) Get BG df                
3) Get SAX encodings   
4) Pre-process the data     
5) Run bolus analysis       Run basal analysis
'''

# Save output to a results folder
d6tflow.set_dir("../results")
# Path to the input file
path = str(Path(__file__).parent.parent) + "/data/risk-data-sample.csv"


''' Load the data at "path" into a Pandas dataframe '''
class TaskGetInitialData(d6tflow.tasks.TaskCSVPandas):
    def run(self):
        initial_df = pd.read_csv(path)
        self.save(initial_df)


''' 
Load the blood glucose data into a Pandas dataframe 
This script also:
    - normalizes the BG data to a particular time interval (defaults to 5 minutes)
    - fills missing values with -1
    - takes the base 10 log of the BG values for use in further analysis
'''
class TaskGetBGData(d6tflow.tasks.TaskCSVPandas):
    def requires(self):
        return TaskGetInitialData()
    
    def run(self):
        df = self.input().load()
        bgs = read_bgs_from_df(df)
        self.save(bgs)


''' Assign SAX values to a dataframe of BG data into a column labeled "bin" '''
class TaskGetSAX(d6tflow.tasks.TaskCSVPandas):
    def requires(self):
        return TaskGetBGData()
    
    def run(self):
        bgs = self.input().load()
        bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)
        sax_encodings = get_sax_encodings(bgs)
        self.save(sax_encodings)


''' 
Preprocess dose data for use in machine learning 

This script:
    - extracts all basals and boluses
    - fills in missing data
    - calculates the TDD for every day in the df, 
      and assigns it to rows from that day
    - Finds the BGs from 3 hours before and after the doses
    - Calculates the minutes of missing BG data from before/after the doses
    - Fills missing bgInput values with CGM data (if avaliable), or the median CGM value
    - Calculates the SAX string representation of BGs for the 3 hours before/after the dose
'''
class TaskPreprocessData(d6tflow.tasks.TaskCSVPandas):
    def requires(self):
        return {
            "raw_df": TaskGetInitialData(), 
            "bg_df": TaskGetBGData(), 
            "sax_df": TaskGetSAX()
        }
    
    def run(self):
        initial_df, bgs, sax_df = self.inputLoad()
        initial_df["time"] = pd.to_datetime(initial_df["time"], infer_datetime_format=True)
        bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)
        sax_df["time"] = pd.to_datetime(sax_df["time"], infer_datetime_format=True)
        processed_doses = preprocess_dose_data(initial_df, bgs, sax_df)
        self.save(processed_doses)


'''
Identify abnormal boluses using a k-nearest neighbors clustering algorithm.
This script trains the model using the "totalBolusAmount", "carbInput", 
"insulinCarbRatio", "bgInput", "insulinSensitivity", and "TDD" columns
'''
class TaskGetAbnormalBoluses(d6tflow.tasks.TaskCSVPandas):
    def requires(self):
        return TaskPreprocessData()
    
    def run(self):
        doses = self.input().load()
        doses["time"] = pd.to_datetime(doses["time"], infer_datetime_format=True)
        abnormal_boluses = find_abnormal_boluses(doses)
        self.save(abnormal_boluses)


'''
Identify abnormal temporary basals using a k-nearest neighbors clustering algorithm.
This script trains the model using the "duration", "percent", and "rate" columns
'''
class TaskGetAbnormalBasals(d6tflow.tasks.TaskCSVPandas):
    def requires(self):
        return TaskPreprocessData()
    
    def run(self):
        doses = self.input().load()
        doses["time"] = pd.to_datetime(doses["time"], infer_datetime_format=True)
        abnormal_basals = find_abnormal_temp_basals(doses)
        self.save(abnormal_basals)

print("Starting tasks...")

''' Uncomment line below to force all tasks to be re-run if called '''
# TaskGetInitialData().invalidate()
''' Uncomment line below to force computations for the preprocessing to be re-run if called '''
# TaskPreprocessData().invalidate()
''' Uncomment lines below to force computations for abnormal boluses & basals to be re-run if called '''
# TaskGetAbnormalBoluses().invalidate()
# TaskGetAbnormalBasals().invalidate()

''' Uncomment line below to find the abnormal boluses '''
d6tflow.run(TaskGetAbnormalBoluses())
''' Uncomment line below to find the abnormal basals '''
# d6tflow.run(TaskGetAbnormalBasals())
''' Uncomment line below to process the dose data '''
# d6tflow.run(TaskPreprocessData())

