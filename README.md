# Tools for performing risk analysis on Tidepool data

## Running the Virtual Environment
### To recreate the Virtual Environment
1. This environment was developed with Anaconda. You'll need to install [Miniconda](https://conda.io/miniconda.html) or [Anaconda](https://anaconda-installer.readthedocs.io/en/latest/) for your platform.
2. In a terminal, navigate to the directory where the environment.yml 
is located (likely the diabetes-risk-analysis folder).
3. Run `conda env create`; this will download all of the package dependencies
and install them in a virtual environment named risk-analysis. PLEASE NOTE: this
may take up to 30 minutes to complete.

### To use the Virtual Environment
In Bash run `source activate risk-analysis`, or in the Anaconda Prompt
run `conda activate risk-analysis` to start the environment.

Run `deactivate` to stop the environment.

## Using the Tools
### File Formatting & Information
`optimized_analysis_pipeline.py` can process an export of Tidepool data and identify the outliers in the data. Currently, this export must include CGM data and insulin dosing data. More specifically, the following columns should be present in the data:

#### Columns:
"type" (type of data: CBG, basal, bolus, etc)

"time" (time of the event)

"subType" (subtype of bolus: normal, extended, dual wave)

"deliveryType" (type of basal: scheduled (according to programmed basal schedule) vs temp)

"normal" (units of insulin delivered via a "normal" bolus)

"extended" (units of insulin delivered via an extended bolus)

"rate" (absolute basal rate)

"insulinCarbRatio" (insulin to carb ratio)

"carbInput" (number of carbs input into bolus calculator)

"insulinOnBoard" (insulin on board)

"bgInput" (input BG into the dose calculator)

"insulinSensitivity" (insulin to BG ratio)

"duration" (temp basal length)

"percent" (percent of basal rate)

"value" (CGM reading in mmol/L)

Not all of these fields are filled for every dosing type. For example, boluses can have information in "type", "time", "normal", "subType", "normal", "extended", "insulinCarbRatio", "carbInput", "insulinOnBoard", "bgInput", and "insulinSensitivity".

#### Configuring the Run
To input the path to the file, edit the `path` variable in `optimized_analysis_pipeline.py`. You should include the absolute path to the csv file (for example on Mac, `/Users/juliesmith/Downloads/diabetes-risk-analysis/raw_data.csv`). The program will check that this path is correct before importing the file. 

At the bottom of `optimized_analysis_pipeline.py`, you can uncomment certain lines of code to mark that parts (or all) of the analysis should be re-run. By default, d6tflow will not re-run operations that have already been performed; for example, if the dose-processing task had already been run (and generated an output), you would need to uncomment `TaskPreprocessData().invalidate()` if you wanted to allow the processing to be re-run. This will also mean that all processes that rely on `TaskPreprocessData` would be re-run if called. This invalidation is specific to the particular 'configuration' of the task - if the task has configuration variables, you must ensure you uncomment the version with those variables in it. If we wanted to run `TaskGetAbnormalBoluses(model_type="isolation_forest")`, you'd need to invalidate the version with `model_type="isolation_forest"`; invalidating `TaskGetAbnormalBoluses()` would have no effect.

Note that you must also `run` the task in order for it to execute; if we wanted to run (or re-run) the abnormal bolus classifier, we'd uncomment `d6tflow.run(TaskGetAbnormalBoluses())`. Running the whole pileline on a file with ~63,000 entries takes roughly 40-50 seconds.

If you run into the situation where the code is not running the tasks as intended, more information about task-run configuration can be found in the documentation at https://d6tflow.readthedocs.io/en/latest/.

#### Output
Outputs for the tasks are saved to individual folders (per task) within a `results` folder. If we wanted to find the csv output file from the abnormal bolus task, that would be contained in `results/TaskGetAbnormalBoluses`.

### Using the graphing tools
<a href="/img/sample_bg_plot.png"><img src="/img/sample_bg_plot.png?raw=true" alt="Sample BG Figure from Tool"></a>
The file `visualize_bg_plots.py` can take csv files that have been run through the dose pre-processing script (`preprocess_data.py`) and visualize the BG values surrounding the event. Upon running, you will be prompted for the *absolute* path to the csv file (example Mac path: `/Users/juliesmith/Downloads/diabetes-risk-analysis/results/processed_doses.csv`), and the row number you'd like to be visualized. The indexing for the row number is how Excel and similar programs index the csv - with the header being index 1, and the first 'actual' line of data values being at index 2. Once you enter the line number, a graph will pop up with the results; close that graph to be prompted for a new line number. Enter any non-valid line number to quit the program.

## Information on Data Fields
Not all of the fields below are present for every type of data (ex: basals have a duration, boluses have an associated carb entry)

### Fields
“type”: data type (basal, bolus, CGM value, etc)

“time”: time of the event/reading

“value”: BG reading in mmol/L, multiply by 18 to get it in mg/dL

“subtype”: type of bolus (normal, extended, dual wave)

“normal”: Units delivered via a ’normal’ bolus

“extended”: Units delivered via a form of extended bolus (can be dual wave)

“insulinCarbRatio”: insulin to carb ratio

“carbInput”: number of carbs that were input into bolus calculator

“insulinOnBoard”: IOB at time of event (this isn’t present for all bolus events)

“bgInput”: BG in mmol/L that was put into bolus calculator

“insulinSensitivity”: insulin to BG ratio

“deliveryType”: type of basal (scheduled, aka from the programmed basal schedule, vs temp)

“duration”: length of the basal

“percent”: percent of the regularly-scheduled basal rate

“rate”: the absolute basal rate


This doesn't cover all of the datatypes, but if there’s a field you’re wondering about, there’s a good chance you can get more info at https://developer.tidepool.org/data-model/, which is Tidepool's data model documentation.

