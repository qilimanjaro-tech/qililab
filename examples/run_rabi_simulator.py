"""Run circuit experiment"""
import os
from pathlib import Path

import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX

from qililab import Experiment, build_platform

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_rabi_simulator():
    """Run Rabi sequence in the fluxqubit simulator."""
    platform = build_platform(name="flux_qubit_simulator")
    circuits = []
    angles = np.linspace(0, np.pi * 2, 20)
    for angle in angles:
        circuit = Circuit(1)
        circuit.add(RX(0, angle))
        circuits.append(circuit)
    experiment = Experiment(platform=platform, sequences=circuits)
    _ = experiment.execute()
    print("success")


if __name__ == "__main__":
    run_rabi_simulator()
