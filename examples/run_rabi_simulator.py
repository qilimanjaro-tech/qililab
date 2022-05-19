"""Run circuit experiment"""
import matplotlib.pyplot as plt
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, M
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME

# configuration = ConnectionConfiguration(
#     user_id=3,
#     username="qili-admin-test",
#     api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
# )

# connection = API(configuration=configuration)


def load_experiment():
    """Load the platform 'platform_0' from the DB."""
    # Using PLATFORM_MANAGER_DB
    circuits = []
    angles = np.linspace(0, np.pi * 2, 20)
    for angle in angles:
        circuit = Circuit(1)
        circuit.add(RX(0, angle))
        circuits.append(circuit)
    experiment = Experiment(platform_name="flux_qubit", sequences=circuits)
    experiment.execute()


if __name__ == "__main__":
    load_experiment()
