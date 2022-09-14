"""Run circuit experiment"""
import argparse
import glob
import os
from pathlib import Path
from typing import List

from qililab import load
from qililab.constants import EXPERIMENT_FILENAME, RESULTS_FILENAME
from qililab.utils.load_data import update_results_files_format

os.environ["DATA"] = str(Path(__file__).parent / "data")

DEFAULT_PATH = "./examples/data/"
RESULTS_FILENAME_BACKUP = "results_bak.yml"
EXPERIMENT_FILENAME_BACKUP = "experiment_bak.yml"


def check_string_included_in_list_strings(text: str, words: List[str]) -> bool:
    """check if a string is included in a list of strings"""
    return any(text in word for word in words)


def files_already_formatted(directory: str) -> bool:
    """check if the files inside the given directory have already been formatted"""
    files = glob.glob(os.path.join(Path(directory), "*"))
    if (
        check_string_included_in_list_strings(text=RESULTS_FILENAME, words=files)
        and check_string_included_in_list_strings(text=RESULTS_FILENAME_BACKUP, words=files)
        and check_string_included_in_list_strings(text=EXPERIMENT_FILENAME, words=files)
        and check_string_included_in_list_strings(text=EXPERIMENT_FILENAME_BACKUP, words=files)
    ):
        print(f"Skipping {directory}")
        return True
    return False


def format_results(path: str):
    """Format all results files to the latest qililab version"""
    directories = glob.glob(os.path.join(path, "*"))
    if not directories:
        raise ValueError("No previous directories data found.")
    for directory in directories:
        files_or_directories = glob.glob(os.path.join(Path(directory), "*"))
        if not files_or_directories or len(files_or_directories) <= 0:
            raise ValueError("No previous results data found.")
        if not os.path.isdir(files_or_directories[0]):
            if not files_already_formatted(directory=directory):
                print(f"Formating {directory}")
                update_results_files_format(path=directory)
            continue
        for nested_directory in files_or_directories:
            if not files_already_formatted(directory=nested_directory):
                print(f"Formating {nested_directory}")
                update_results_files_format(path=nested_directory)


def load_one_result(path: str):
    """Load one result"""
    _, results = load(path=path)
    acquisitions = results.acquisitions(mean=False)
    print(acquisitions)


def load_results(path: str):
    """Load all formatted results"""
    directories = glob.glob(os.path.join(path, "*"))
    if not directories:
        raise ValueError("No previous directories data found.")
    for directory in directories:
        files_or_directories = glob.glob(os.path.join(Path(directory), "*"))
        if not files_or_directories or len(files_or_directories) <= 0:
            raise ValueError("No previous results data found.")
        if not os.path.isdir(files_or_directories[0]):
            print(f"Loading {directory}")
            load_one_result(path=directory)
            continue
        for nested_directory in files_or_directories:
            print(f"Loading {nested_directory}")
            load_one_result(path=nested_directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format results to the latest qililab version")
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        required=False,
        metavar="<PATH>",
        help="Relative path from where the executable is run",
    )
    args = parser.parse_args()
    input_path: str = args.path if "path" in args and args.path is not None else DEFAULT_PATH
    format_results(path=input_path)
    # load_results(path=input_path)
