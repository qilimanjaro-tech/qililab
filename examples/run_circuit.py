"""Run circuit experiment"""
import matplotlib.pyplot as plt
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
    # Using PLATFORM_MANAGER_DB
    circuit = Circuit(1)
    circuit.add(X(0))
    circuit.add(RX(0, 20))
    circuit.add(M(0))
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequence=circuit)
    # experiment.add_parameter_to_loop(
    #     category="signal_generator", id_=1, parameter="frequency", start=7.345e9, stop=7.35e9, num=1000
    # )
    experiment.draw()
    plt.show()


if __name__ == "__main__":
    load_experiment()
