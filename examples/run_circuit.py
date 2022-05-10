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
    # Using PLATFORM_MANAGER_DB
    circuit = Circuit(1)
    # circuit.add(X(0))
    circuit.add(M(0))
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequence=circuit, connection=connection)
    experiment.add_parameter_to_loop(
        category="signal_generator", id_=1, parameter="frequency", start=7300000000.0, stop=7313000000.0, num=50
    )
    results = experiment.execute()
    voltages = [result[0].voltages() for result in results]
    plt.plot(voltages)
    plt.savefig(fname="test.png")


if __name__ == "__main__":
    load_experiment()
