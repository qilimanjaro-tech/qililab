"""Run circuit experiment"""
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, I, M, X
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.typings import Category, Parameter
from qililab.utils import Loop

configuration = ConnectionConfiguration(
    user_id=3,
    username="qili-admin-test",
    api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
)

connection = API(configuration=configuration)


def run_experiment(gate: str, category: str, id_: int, parameter: str, start: float, stop: float, num: int):
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
    loop = Loop(category=Category(category), id_=id_, parameter=Parameter(parameter), start=start, stop=stop, num=num)
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=circuit, loop=loop)
    experiment.execute(connection=connection)
