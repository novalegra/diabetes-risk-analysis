# Tools for performing risk analysis on Tidepool data

## Running the Virtual Environment
### To recreate the Virtual Environment
1. This environment was developed with Anaconda. You'll need to install [Miniconda](https://conda.io/miniconda.html) or [Anaconda](https://anaconda-installer.readthedocs.io/en/latest/) for your platform.
2. In a terminal, navigate to the directory where the environment.yml 
is located (likely the diabetes-risk-analysis folder).
3. Run `conda env create`; this will download all of the package dependencies
and install them in a virtual environment named tda-dev. PLEASE NOTE: this
may take up to 30 minutes to complete.

### To use the Virtual Environment
In Bash run `source activate tda-dev`, or in the Anaconda Prompt
run `conda activate tda-dev` to start the environment.

Run `deactivate` to stop the environment.

## Using the Tools
TODO

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

“carbInput”: number of carbs (I believe that were input into bolus calculator)

“insulinOnBoard”: IOB at time of event, this isn’t present for all the bolus events

“bgInput”: BG that was put into bolus calculator in mmol/L

“insulinSensitivity”: insulin to BG ratio

“deliveryType”: type of basal (scheduled, aka from the programmed basal schedule, vs temp)

“duration”: length of the basal

“percent”: percent of the regularly-scheduled basal rate

“rate”: the absolute basal rate


This doesn't cover all of the datatypes, but if there’s a field you’re wondering about, there’s a good chance you can get more info at https://developer.tidepool.org/data-model/, which is Tidepool's data model documentation.

