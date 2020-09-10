import multiprocessing
import d6tflow
import d6tcollect

from os import listdir
from os.path import exists, isdir, join
import optimized_analysis_pipeline as p

d6tcollect.submit = False  # Turn off automatic error reporting
d6tflow.settings.log_level = "ERROR"  # Decrease console printout
d6tflow.set_dir("../results")  # Save output to a results folder

def find_csv_filenames(path_to_dir, suffix=".csv"):
    """ Find all csv filenames in given dir """
    file_names = listdir(path_to_dir)
    return [join(path_to_dir, filename) for filename in file_names if filename.endswith(suffix)]


def is_valid(path):
    """ Check if a file is valid, and print an appropriate error message """
    if not exists(path):
        print(path, "is invalid file path")
        return False
    return True


def is_directory(path):
    """ Check if path is valid directory, and print an appropriate error message """
    if not isdir(path):
        print(path, "is not a directory")
        return False
    return True


def process_one_file(file_path):
    """ Run the processing pipeline on one file """
    # Create a identifier based on the file path
    identifier = file_path.split("/")[-1]

    """ Uncomment these lines depending on what the 'aim' of the processing is, and what steps should be re-run """

    """ Uncomment line below to mark that all tasks should be re-run """
    p.TaskGetInitialData(path=file_path, identifier=identifier).invalidate(confirm=False)
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
    d6tflow.run(p.TaskGetAbnormalBoluses(path=file_path, model_type="knn", identifier=identifier))
    """ Uncomment line below to find the abnormal boluses using an Isolation Forest model """
    # d6tflow.run(p.TaskGetAbnormalBoluses(path=file_path, model_type="isolation_forest", identifier=identifier))
    """ Uncomment line below to find the abnormal basals """
    # d6tflow.run(p.TaskGetAbnormalBasals(path=file_path, identifier=identifier))
    """ Uncomment line below to process the dose data """
    # d6tflow.run(p.TaskPreprocessData(path=file_path, identifier=identifier))


def process_files(input_file_path):
    """ Run the processing pipeline on the files contained in the txt file at 'input_file_path' """
    with open(input_file_path) as f:
        # Each file path is in its own line
        for file_path in f:
            # Get rid of whitespace/new lines
            file_path = file_path.rstrip()
            if is_valid(file_path):
                pool.apply_async(process_one_file, [file_path])

def process_files_from_dir(input_dir):
    """ Run the processing pipeline on the files contained in the txt file at 'input_file_path' """
    files = find_csv_filenames(input_dir)
    for file_path in files:
        # Get rid of whitespace/new lines
        file_path = file_path.rstrip()
        if is_valid(file_path):
            pool.apply_async(process_one_file, [file_path])



if __name__ == "__main__":
    """
    Two options: either specify a directory to pull the files from,
    or a file containing all the paths to the .csvs to process
    """
    option = input("Process all files in directory (1) or file paths in an input file (2)? ")
    while option not in ["1", "2"]:
        print("Invalid input; you must enter '1' or '2'")
        option = input("Process all files in directory (1) or file paths in an input file (2)? ")
    
    # Use multiprocessing to decrease processing time
    pool = multiprocessing.Pool()
    if option == "1": # Files in directory
        input_dir = "/Users/annaquinlan/Downloads/csv"#input("Input file path: ")
        while not is_directory(input_dir):
            input_dir = input("Input directory path: ")
        process_files_from_dir(input_dir)
    else: # Files paths from input file
        # Get the input file path
        input_file = "/Users/annaquinlan/Desktop/diabetes-risk-analysis/data/files_to_process.txt"#input("Input file path: ")
        while not is_valid(input_dir):
            input_file = input("Input file path: ")
        process_files(input_file)

    pool.close()
    pool.join()
