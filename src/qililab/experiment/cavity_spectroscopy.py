from qibo.core.circuit import Circuit
from qibo.gates import I, M
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab.experiment import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME

configuration = ConnectionConfiguration(
    user_id=3,
    username="qili-admin-test",
    api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
)

connection = API(configuration=configuration)

def cavity_spectroscopy(connection: API):
    """Perform a Rabi spectroscopy."""
    circuit = Circuit(1)
    circuit.add(I(0))  # need to add this to use QCM (because QRM uses QCM clock)
    circuit.add(M(0))
    settings = Experiment.ExperimentSettings()
    settings.readout_pulse.amplitude = 1
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequence=circuit, connection=connection, settings=settings)
    experiment.add_parameter_to_loop(
        category="signal_generator", id_=1, parameter="frequency", start=7.34e9, stop=7.36e9, num=1000
    )
    experiment.execute()


if __name__ == "__main__":
    cavity_spectroscopy(connection=connection)
