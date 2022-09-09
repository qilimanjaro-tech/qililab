"""Run circuit experiment"""
import glob
import os
from pathlib import Path

from qililab import load
from qililab.utils.load_data import update_results_files_format

os.environ["DATA"] = str(Path(__file__).parent / "data")


def format_results():
    """Format all results files to the latest qililab version"""
    directories = glob.glob(os.path.join("./examples/data/", "*"))
    if not directories:
        raise ValueError("No previous directories data found.")
    for directory in directories:
        files_or_directories = glob.glob(os.path.join(Path(directory), "*"))
        if not files_or_directories or len(files_or_directories) <= 0:
            raise ValueError("No previous results data found.")
        if not os.path.isdir(files_or_directories[0]):
            print(f"Formating {directory}")
            update_results_files_format(path=directory)
            continue
        for nested_directory in files_or_directories:
            print(f"Formating {nested_directory}")
            update_results_files_format(path=nested_directory)


def load_one_result(path: str):
    """Load one result"""
    _, results = load(path=path)
    acquisitions = results.acquisitions(mean=False)
    print(acquisitions)


def load_results():
    """Load all formatted results"""
    directories = glob.glob(os.path.join("./examples/data/", "*"))
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
    format_results()
    load_results()
