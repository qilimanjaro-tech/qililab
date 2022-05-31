"""Qubit spectroscopy."""
from qibo.core.circuit import Circuit
from qibo.gates import M, X
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment
from qililab.utils import Loop


def qubit_spectroscopy(connection: API):
    """Load the platform 'platform_0' from the DB."""
    # Using PLATFORM_MANAGER_DB
    circuit = Circuit(1)
    # circuit.add(X(0))
    circuit.add(X(0))
    circuit.add(M(0))
    experiment = Experiment(
        platform_name=DEFAULT_PLATFORM_NAME, sequences=[circuit], experiment_name="qubit_spectroscopy"
    )
    loop = Loop(category="signal_generator", id_=0, parameter="frequency", start=3.64e9, stop=3.69e9, num=1000)
    experiment.execute(loops=loop, connection=connection)


if __name__ == "__main__":
    configuration = ConnectionConfiguration(
        user_id=3,
        username="qili-admin-test",
        api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
    )

    api = API(configuration=configuration)
    qubit_spectroscopy(connection=api)
