"""Run circuit experiment"""
import matplotlib.pyplot as plt
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import M, X, Y, I, RX
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
    # circuits = []
    # for rotation in np.linspace(0, 3*np.pi):
    #     circuit = Circuit(1)
    #     circuit.add(RX(0), rotation)
    #     circuit.add(M(0))
    #     circuits.append(circuit)
    circuit = Circuit(1)
    circuit.add(X(0))
    circuit.add(M(0))
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=circuit)
    experiment.set_parameter(category="signal_generator", id_=0, parameter="frequency", value=3.451759e9)
    experiment.set_parameter(category="signal_generator", id_=1, parameter="frequency", value=7.347367e9)
    experiment.add_parameter_to_loop(
        category="qubit_instrument", id_=0, parameter="gain", start=0, stop=1, num=20
    )
    figure = experiment.draw()
    plt.savefig("test.png")
    #experiment.execute(connection=connection)


if __name__ == "__main__":
    load_experiment()
