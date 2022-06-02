"""Run circuit experiment"""
import matplotlib.pyplot as plt
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, I, M, X, Y
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment


def load_experiment(connection: API):
    """Load the platform 'platform_0' from the DB."""
    circuits = []
    for rotation in np.linspace(0, 3*np.pi):
        circuit = Circuit(1)
        circuit.add(RX(0, rotation))
        circuit.add(M(0))
        circuits.append(circuit)
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=circuits)
    experiment.execute(connection=connection)


if __name__ == "__main__":
    configuration = ConnectionConfiguration(
        user_id=3,
        username="qili-admin-test",
        api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
    )

    connection = API(configuration=configuration)
    load_experiment(connection=connection)
