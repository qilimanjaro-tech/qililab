"""Run circuit experiment"""
from qibo.core.circuit import Circuit
from qibo.gates import I, M, X, Y, RX, RY
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration
import numpy as np

from qililab import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME

configuration = ConnectionConfiguration(
    user_id=3,
    username="qili-admin-test",
    api_key="d31d38f4-228e-4898-a0a4-4c4139d0f79f",
)

connection = API(configuration=configuration)


def run_experiment(gate: str, category: str, id_: int, parameter: str, start: float, stop: float, num: int):
    circuit = Circuit(1)
    if gate == "I":
        gate = I(0)
    elif gate == "X":
        gate = X(0)
    elif gate == "RX":
        gate = RX(0, np.pi/2)
    elif gate == "RY":
        gate = RY(0, np.pi/2)
    circuit.add(gate)
    circuit.add(M(0))
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequence=circuit, connection=connection)
    experiment.add_parameter_to_loop(
        category=category, id_=id_, parameter=parameter, start=start, stop=stop, num=num
    )
    experiment.execute()


if __name__ == "__main__":
    run_experiment()
