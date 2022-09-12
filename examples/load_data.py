"""Run circuit experiment"""
import cProfile
import os
from pathlib import Path

from qililab import load
from qililab.utils.load_data import (
    _load_backup_results_file,
    _save_file,
    update_results_files_format,
)

os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit():
    """Load the platform 'galadriel' from the DB."""
    # experiment, results = load(path="./examples/data/20220725_121101_allxy_cmap")
    path = "./examples/data/20220818/105310_qubit_spectroscopy"
    update_results_files_format(path=path)
    _, results = load(path=path)
    acquisitions = results.acquisitions(mean=False)
    print(acquisitions)


def load_save_result():
    """load and save one result"""
    path = "./examples/data/20220722_203146_allxy_cmap"
    result = _load_backup_results_file(path=path)
    _save_file(path=path, data=result, filename="test.yml")


if __name__ == "__main__":
    run_circuit()
    # cProfile.run("load_save_result()")
    # load_save_result()
