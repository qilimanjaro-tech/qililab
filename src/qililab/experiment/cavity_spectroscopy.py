"""Cavity spectroscopy."""
from qibo.core.circuit import Circuit
from qibo.gates import I, M
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment, settings
from qililab.utils import Loop


def cavity_spectroscopy(connection: API):
    """Perform a Rabi spectroscopy."""
    circuit = Circuit(1)
    circuit.add(I(0))  # need to add this to use QCM (because QRM uses QCM clock)
    circuit.add(M(0))
    settings.translation.readout_pulse.amplitude = 1
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=[circuit], settings=settings)
    loop = Loop(category="signal_generator", id_=1, parameter="frequency", start=7.34e9, stop=7.36e9, num=1000)
    experiment.execute(loops=loop, connection=connection)


if __name__ == "__main__":
    configuration = ConnectionConfiguration(
        user_id=3,
        username="qili-admin-test",
        api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
    )

    api = API(configuration=configuration)
    cavity_spectroscopy(connection=api)
