import d6tflow
import d6tcollect
d6tcollect.submit = False # Turn off automatic error reporting
import luigi
import pandas as pd

from pathlib import Path
from os.path import exists

from utils import read_bgs_from_df
from bg_sax_analysis import get_sax_encodings
from preprocess_data import preprocess_dose_data, find_bgs_before_and_after
from bolus_risk_analysis import find_abnormal_boluses
from basal_risk_analysis import find_abnormal_temp_basals

'''
Task Flow:
1) Get initial df
2) Get BG df                
3) Get SAX encodings   
4) Pre-process the data     Pre-process the BGs used for visualizations   
5) Run bolus analysis       Run basal analysis
'''

# Save output to a results folder
d6tflow.set_dir("../results")
# Path to the input file - YOU MUST FILL THIS IN
path = str(Path(__file__).parent.parent) + "/data/random_person.csv"
assert(exists(path))

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
        
        # Convert the times to datetimes
        initial_df["time"] = pd.to_datetime(initial_df["time"], infer_datetime_format=True)
        bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)
        sax_df["time"] = pd.to_datetime(sax_df["time"], infer_datetime_format=True)

        # Run through processing
        processed_doses = preprocess_dose_data(initial_df, bgs, sax_df)
        self.save(processed_doses)


class TaskPreprocessBGs(d6tflow.tasks.TaskCSVPandas):
    def requires(self):
        return {
            "raw_df": TaskGetInitialData(), 
            "bg_df": TaskGetBGData()
        }
    
    def run(self):
        initial_df, bgs = self.inputLoad()
        bgs["time"] = pd.to_datetime(bgs["time"], infer_datetime_format=True)

        # Run through processing
        annotated_doses = find_bgs_before_and_after(initial_df, bgs)
        self.save(annotated_doses)



'''
Identify abnormal boluses using a k-nearest neighbors clustering algorithm.
This script trains the model using the "totalBolusAmount", "carbInput", 
"insulinCarbRatio", "bgInput", "insulinSensitivity", and "TDD" columns
'''
class TaskGetAbnormalBoluses(d6tflow.tasks.TaskCSVPandas):
    model_type = luigi.Parameter(default = "knn")
    def requires(self):
        return {
            "preprocessed_doses": TaskPreprocessData(),
            "bg_annotated_doses": TaskPreprocessBGs()
        }
    
    def run(self):
        doses, bgs = self.inputLoad()
        doses["time"] = pd.to_datetime(doses["time"], infer_datetime_format=True)

        # Merge in the relevent BG data
        doses["bgs_before"] = bgs["bgs_before"]
        doses["bgs_after"] = bgs["bgs_after"]
        doses["duration_gaps_before"] = bgs["duration_gaps_before"]
        doses["duration_gaps_after"] = bgs["duration_gaps_after"]
        doses["bg_30_min_before"] = bgs["bg_30_min_before"]
        doses["bg_75_min_after"] = bgs["bg_75_min_after"]

        abnormal_boluses = find_abnormal_boluses(doses, self.model_type)
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

''' Uncomment line below to mark that all tasks should be re-run '''
# TaskGetInitialData().invalidate(confirm=False)
''' Uncomment line below to mark that tasks related to BGs should be re-run '''
# TaskGetBGData().invalidate(confirm=False)
''' Uncomment line below to mark that tasks for the preprocessing should be re-run '''
# TaskPreprocessData().invalidate(confirm=False)
# TaskPreprocessBGs().invalidate(confirm=False)
''' Uncomment lines below to mark that tasks to identify abnormal boluses &/or basals with a KNN model should be re-run '''
# TaskGetAbnormalBoluses().invalidate(confirm=False)
# TaskGetAbnormalBasals().invalidate(confirm=False)
''' Uncomment lines below to mark that tasks to identify abnormal boluses with an Isolation Forest model should be re-run '''
# TaskGetAbnormalBoluses(model_type="isolation_forest").invalidate(confirm=False)


''' Uncomment line below to find the abnormal boluses using k-nearest neighbors'''
# d6tflow.run(TaskGetAbnormalBoluses())
''' Uncomment line below to find the abnormal boluses using an Isolation Forest model '''
# d6tflow.run(TaskGetAbnormalBoluses(model_type="isolation_forest"))
''' Uncomment line below to find the abnormal basals '''
# d6tflow.run(TaskGetAbnormalBasals())
''' Uncomment line below to process the dose data '''
# d6tflow.run(TaskPreprocessData())

