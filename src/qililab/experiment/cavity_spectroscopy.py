"""Cavity spectroscopy."""
from qibo.core.circuit import Circuit
from qibo.gates import I, M
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment
from qililab.typings import Category, Parameter
from qililab.utils import Loop


def cavity_spectroscopy(connection: API):
    """Perform a Rabi spectroscopy."""
    circuit = Circuit(1)
    circuit.add(I(0))  # need to add this to use QCM (because QRM uses QCM clock)
    circuit.add(M(0))
    loop = Loop(
        category=Category.SIGNAL_GENERATOR, id_=1, parameter=Parameter.FREQUENCY, start=7.34e9, stop=7.36e9, num=1000
    )
    experiment = Experiment(
        platform_name=DEFAULT_PLATFORM_NAME,
        sequences=[circuit],
        loop=loop,
        experiment_name="cavity_spectroscopy",
    )
    experiment.set_parameter(category="platform", id_=0, parameter="readout_amplitude", value=1)
    experiment.execute(connection=connection)


if __name__ == "__main__":
    configuration = ConnectionConfiguration(
        user_id=3,
        username="qili-admin-test",
        api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
    )

    api = API(configuration=configuration)
    cavity_spectroscopy(connection=api)
