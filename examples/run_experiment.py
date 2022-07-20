"""Run circuit experiment"""
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, I, M, X
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import Experiment, build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.typings import Instrument, Parameter
from qililab.utils import Loop

configuration = ConnectionConfiguration(
    username="a-valid-user",
    api_key="a-valid-password",
)

connection = API(configuration=configuration)


def run_experiment(gate: str, instrument: str, id_: int, parameter: str, start: float, stop: float, num: int):
    """Run experiment."""
    circuit = Circuit(1)
    if gate == "I":
        gate = I(0)
    elif gate == "X":
        gate = X(0)
    elif gate == "RX":
        gate = RX(0, np.pi / 2)
    elif gate == "RY":
        gate = RY(0, np.pi / 2)
    circuit.add(gate)
    circuit.add(M(0))
    platform = build_platform(name=DEFAULT_PLATFORM_NAME)
    loop = Loop(
        instrument=Instrument(instrument), id_=id_, parameter=Parameter(parameter), start=start, stop=stop, num=num
    )
    experiment = Experiment(connection=connection, platform=platform, sequences=circuit, loop=loop)
    experiment.execute()
