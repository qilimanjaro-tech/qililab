"""Run circuit experiment"""
import os
from pathlib import Path

import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, M
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment
from qililab.typings import Parameter
from qililab.utils import Loop

os.environ["RUNCARDS"] = str(Path(__file__).parent)
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit(connection: API | None = None):
    """Load the platform 'galadriel' from the DB."""
    platform = build_platform(name=DEFAULT_PLATFORM_NAME)
    circuits = []
    for rotation in np.linspace(0, 3 * np.pi, 2):
        circuit = Circuit(1)
        circuit.add(RX(0, rotation))
        circuit.add(M(0))
        circuits.append(circuit)
    loop = Loop(alias="resonator", parameter=Parameter.FREQUENCY, start=7.314e9, stop=7.332e9, step=0.1e6)
    experiment = Experiment(platform=platform, sequences=circuits, loop=loop)
    results = experiment.execute(connection=connection)
    print(results.acquisitions())


if __name__ == "__main__":
    # configuration = ConnectionConfiguration(  # pylint: disable=no-value-for-parameter
    #     username="test-username", api_key="test-api-key"
    # )
    # api = API(configuration=configuration)
    run_circuit()
