"""Run circuit experiment"""
import os
from pathlib import Path

from qibo.core.circuit import Circuit
from qibo.gates import M
from qiboconnection.api import API

from qililab import build_platform
from qililab.experiment import Experiment
from qililab.typings import Parameter
from qililab.utils import Loop

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit(connection: API | None = None):
    """Load the platform 'sauron' from the DB."""
    platform = build_platform(name="sauron")
    platform.connect()
    platform.set_parameter(alias="qblox_S4g", parameter=Parameter.CURRENT, value=0.002)


if __name__ == "__main__":

    run_circuit()
