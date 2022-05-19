"""Run circuit experiment"""
import matplotlib.pyplot as plt
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, M, X
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME

configuration = ConnectionConfiguration(
    user_id=3,
    username="qili-admin-test",
    api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
)

connection = API(configuration=configuration)


def load_experiment():
    """Load the platform 'platform_0' from the DB."""
    circuit = Circuit(1)
    circuit.add(X(0))
    experiment = Experiment(platform_name="flux_qubit", sequences=[circuit])
    experiment.add_parameter_to_loop(
        category="system_control", id_=0, parameter="frequency", start=2.08e9, stop=2.0899e9, num=20
    )
    experiment.execute(connection=connection)


if __name__ == "__main__":
    load_experiment()
