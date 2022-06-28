"""Run circuit experiment"""
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, M
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment


def run_circuit(connection: API):
    """Load the platform 'galadriel' from the DB."""
    platform = build_platform(name=DEFAULT_PLATFORM_NAME)
    circuits = []
    for rotation in np.linspace(0, 3 * np.pi, 2):
        circuit = Circuit(1)
        circuit.add(RX(0, rotation))
        circuit.add(M(0))
        circuits.append(circuit)
    experiment = Experiment(platform=platform, sequences=circuits)
    results = experiment.execute(connection=connection)
    print(results.acquisitions())


if __name__ == "__main__":
    configuration = ConnectionConfiguration(  # pylint: disable=no-value-for-parameter
        username="test-username", api_key="test-api-key"
    )
    api = API(configuration=configuration)
    run_circuit(connection=api)
