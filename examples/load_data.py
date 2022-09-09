"""Run circuit experiment"""
import os
from pathlib import Path

from qililab import load
from qililab.utils.load_data import update_results_files_format

os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit():
    """Load the platform 'galadriel' from the DB."""
    # experiment, results = load(path="./examples/data/20220725_121101_allxy_cmap")
    update_results_files_format(path="./examples/data/fail_flip")
    _, results = load(path="./examples/data/fail_flip")
    acquisitions = results.acquisitions(mean=False)
    print(acquisitions)


if __name__ == "__main__":
    run_circuit()
