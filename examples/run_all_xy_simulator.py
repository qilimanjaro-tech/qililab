"""Run circuit experiment"""
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import RX, RY, I
from qibo.models.circuit import Circuit

from qililab import Experiment, build_platform

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_allxy():
    """Run AllXY"""
    platform = build_platform(name="flux_qubit_simulator")

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

    experiment = Experiment(platform=platform, circuits=circuits)
    results = experiment.execute()

    x_ticks = np.linspace(-1, 1, 10)

    for x_tick, loop_results in zip(x_ticks, results):
        prob = np.array([result.probabilities() for result in loop_results])
        plt.plot(prob[:, 0], label=f"{x_tick} MHz")

    labels = [
        "I, I",
        "X180, X180",
        "Y180, Y180",
        "X180, Y180",
        "Y180, X180",
        "X90, I",
        "Y90, I",
        "X90, Y90",
        "Y90, X90",
        "X90, Y180",
        "Y90, X180",
        "X180, Y90",
        "Y180, X90",
        "X90, X180",
        "X180, X90",
        "Y90, Y180",
        "Y180, Y90",
        "X180, I",
        "Y180, I",
        "X90, X90",
        "Y90, Y90",
    ]
    plt.legend()
    plt.grid()
    plt.xticks(np.arange(0, 21, 1), labels, rotation=70)
    plt.show()


if __name__ == "__main__":
    run_allxy()
