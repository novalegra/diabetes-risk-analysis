import multiprocessing
import d6tflow
import d6tcollect

from os.path import exists
import optimized_analysis_pipeline as p

d6tcollect.submit = False  # Turn off automatic error reporting
d6tflow.settings.log_level = "ERROR"  # Decrease console printout
d6tflow.set_dir("../results")  # Save output to a results folder


""" Check if a file is valid, and print an appropriate error message """


def is_valid(path):
    if not exists(path):
        print(path, "is invalid file path")
        return False
    return True


""" Run the processing pipeline on one file """


def process_one_file(file_path):
    # Create a identifier based on the file path
    identifier = file_path.split("/")[-1]

    """ Uncomment these lines depending on what the 'aim' of the processing is, and what steps should be re-run """

    """ Uncomment line below to mark that all tasks should be re-run """
    # p.TaskGetInitialData(path=file_path, identifier=identifier).invalidate(confirm=False)
    """ Uncomment line below to mark that tasks related to BGs should be re-run """
    # p.TaskGetBGData(path=file_path, identifier=identifier).invalidate(confirm=False)
    """ Uncomment line below to mark that tasks for the preprocessing should be re-run """
    # p.TaskPreprocessData(path=file_path, identifier=identifier).invalidate(confirm=False)
    # p.TaskPreprocessBGs(path=file_path, identifier=identifier).invalidate(confirm=False)
    """ Uncomment lines below to mark that tasks to identify abnormal boluses &/or basals with a KNN model should be re-run """
    # p.TaskGetAbnormalBoluses(path=file_path, model_type="knn", identifier=identifier).invalidate(confirm=False)
    # p.TaskGetAbnormalBasals(path=file_path, identifier=identifier).invalidate(confirm=False)
    """ Uncomment lines below to mark that tasks to identify abnormal boluses with an Isolation Forest model should be re-run """
    # p.TaskGetAbnormalBoluses(path=file_path, model_type="isolation_forest", identifier=identifier).invalidate(confirm=False)

    """ Uncomment line below to find the abnormal boluses using k-nearest neighbors"""
    # d6tflow.run(p.TaskGetAbnormalBoluses(path=file_path, model_type="knn", identifier=identifier))
    """ Uncomment line below to find the abnormal boluses using an Isolation Forest model """
    # d6tflow.run(p.TaskGetAbnormalBoluses(path=file_path, model_type="isolation_forest", identifier=identifier))
    """ Uncomment line below to find the abnormal basals """
    # d6tflow.run(p.TaskGetAbnormalBasals(path=file_path, identifier=identifier))
    """ Uncomment line below to process the dose data """
    # d6tflow.run(p.TaskPreprocessData(path=file_path, identifier=identifier))


""" Run the processing pipeline on the files contained in the txt file at 'input_file_path' """


def process_files(input_file_path):
    with open(input_file_path) as f:
        # Each file path is in its own line
        for file_path in f:
            # Get rid of whitespace/new lines
            file_path = file_path.rstrip()
            if is_valid(file_path):
                pool.apply_async(process_one_file, [file_path])


if __name__ == "__main__":
    # Get the input file path
    input_file = "/Users/annaquinlan/Desktop/diabetes-risk-analysis/data/files_to_process.txt"#input("Input file path: ")
    while not is_valid(input_file):
        input_file = input("Input file path: ")

    # Use multiprocessing to decrease processing time
    pool = multiprocessing.Pool()
    process_files(input_file)
    pool.close()
    pool.join()
