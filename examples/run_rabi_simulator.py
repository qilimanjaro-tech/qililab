"""Run circuit experiment"""
import numpy as np
from qibo.core.circuit import Circuit
from qibo.gates import RX

from qililab import Experiment


def run_rabi_simulator():
    """Run Rabi sequence in the fluxqubit simulator."""
    circuits = []
    angles = np.linspace(0, np.pi * 2, 20)
    for angle in angles:
        circuit = Circuit(1)
        circuit.add(RX(0, angle))
        circuits.append(circuit)
    experiment = Experiment(platform_name="flux_qubit", sequences=circuits)
    experiment.execute()


if __name__ == "__main__":
    run_rabi_simulator()
