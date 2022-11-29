"""Run circuit experiment"""
import os
from pathlib import Path

from qibo.core.circuit import Circuit
from qibo.gates import M, X
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import build_platform, load
from qililab.experiment import Experiment
from qililab.typings import Parameter
from qililab.utils import Loop

# os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
# os.environ["DATA"] = str(Path(__file__).parent / "data")


def load_result(path: str):
    """Load the platform 'galadriel' from the DB."""
    experiment, results = load(path=path)  # last file is loaded when no path is given
    print(experiment)
    print(results)


if __name__ == "__main__":
    path = "/home/jupytershared/data/20221128/153357_cavity_spectroscopy"
    load_result(path=path)
