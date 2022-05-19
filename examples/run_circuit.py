"""Run circuit experiment"""
import matplotlib.pyplot as plt
from qibo.core.circuit import Circuit
from qibo.gates import I, M, X, Y
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
    # circuit = Circuit(1)
    # circuit.add(X(0))
    # circuit.add(Y(0))
    # circuit.add(M(0))
    circuit = Circuit(2)
    circuit.add(X(0))
    circuit.add(Y(0))
    circuit.add(M(0))
    circuit.add(I(1))
    circuit.add(X(1))
    circuit.add(M(1))
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=[circuit])
    print(experiment.parameters)
    experiment.add_parameter_to_loop(
        category="signal_generator", id_=0, parameter="frequency", start=2.08e9, stop=2.0899e9, num=20
    )
    # experiment.execute(connection=connection)
    experiment.draw()
    plt.show()


if __name__ == "__main__":
    load_experiment()
