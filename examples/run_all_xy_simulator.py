"""Run circuit experiment"""
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, I

from qililab import Experiment


def run_allxy():
    """Run AllXY"""
    circuits = []
    allxy_table = [
        [I(0), I(0)],
        [RX(0, np.pi), RX(0, np.pi)],
        [RY(0, np.pi), RY(0, np.pi)],
        [RX(0, np.pi), RY(0, np.pi)],
        [RY(0, np.pi), RX(0, np.pi)],
        [RX(0, np.pi / 2), I(0)],
        [RY(0, np.pi / 2), I(0)],
        [RX(0, np.pi / 2), RY(0, np.pi / 2)],
        [RY(0, np.pi / 2), RX(0, np.pi / 2)],
        [RX(0, np.pi / 2), RY(0, np.pi)],
        [RY(0, np.pi / 2), RX(0, np.pi)],
        [RX(0, np.pi), RY(0, np.pi / 2)],
        [RY(0, np.pi), RX(0, np.pi / 2)],
        [RX(0, np.pi / 2), RX(0, np.pi)],
        [RX(0, np.pi), RX(0, np.pi / 2)],
        [RY(0, np.pi / 2), RY(0, np.pi)],
        [RY(0, np.pi), RY(0, np.pi / 2)],
        [RX(0, np.pi), I(0)],
        [RY(0, np.pi), I(0)],
        [RX(0, np.pi / 2), RX(0, np.pi / 2)],
        [RY(0, np.pi / 2), RY(0, np.pi / 2)],
    ]
    for gate_pair in allxy_table:
        circuit = Circuit(1)
        circuit.add(gate_pair[0])
        circuit.add(gate_pair[1])
        circuits.append(circuit)

    experiment = Experiment(platform_name="flux_qubit", sequences=circuits)
    experiment.add_parameter_to_loop(
        category="system_control",
        id_=0,
        parameter="frequency",
        start=2089351224.5666978,
        stop=2089351224.5666978 + 10e6,
        num=20,
    )
    experiment.execute()


if __name__ == "__main__":
    run_allxy()
