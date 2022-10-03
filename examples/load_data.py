"""Run circuit experiment"""
import os
from pathlib import Path

from qililab import load

os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit():
    """Load the platform 'galadriel' from the DB."""
    # experiment, results = load(path="./examples/data/20220725_121101_allxy_cmap")
    path = "../../qili_data/20220621_155154_punchout"
    _, results = load(path=path)
    acquisitions = results.acquisitions(mean=False)
    print(acquisitions)


if __name__ == "__main__":
    run_circuit()
