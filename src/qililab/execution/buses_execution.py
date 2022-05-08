"""BusesExecution class."""
from dataclasses import dataclass, field
from itertools import zip_longest
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

from qililab.execution.bus_execution import BusExecution
from qililab.gates import HardwareGate


@dataclass
class BusesExecution:
    """BusesExecution class."""

    buses: List[BusExecution] = field(default_factory=list)

    def connect(self):
        """Connect to the instruments."""
        for bus in self.buses:
            bus.connect()

    def setup(self):
        """Setup instruments with experiment settings."""
        for bus in self.buses:
            bus.setup()

    def start(self):
        """Start/Turn on the instruments."""
        for bus in self.buses:
            bus.start()

    def run(self):
        """Run the given pulse sequence."""
        results = []
        for bus in self.buses:
            result = bus.run()
            if result is not None:
                results.append(result)

        return results

    def close(self):
        """Close connection to the instruments."""
        for bus in self.buses:
            bus.close()

    def pulses(self, resolution: float = 1.0):
        """Get pulses of each bus and sum pulses by their qubit id.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Dict[int, np.ndarray]: Dictionary containing a list of the I/Q amplitudes of the control and readout
            pulses applied on each qubit.
        """
        pulses: Dict[int, np.ndarray] = {}
        for bus in self.buses:
            new_pulses = np.array(bus.pulses(resolution=resolution))
            for qubit_id in bus.qubit_ids:
                if qubit_id not in pulses:
                    pulses[qubit_id] = new_pulses
                    continue
                old_pulses = pulses[qubit_id]
                pulses[qubit_id] = np.array(
                    [[x + y for x, y in zip_longest(old, new, fillvalue=0)] for old, new in zip(old_pulses, new_pulses)]
                )

        return pulses

    def draw(self, resolution: float, num_qubits: int):
        """Save figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        figure, axes = plt.subplots(num_qubits, 1)
        if num_qubits == 1:
            axes = [axes]  # make axes subscriptable
        for idx, pulse in self.pulses(resolution=resolution).items():
            time = np.arange(len(pulse[0])) * resolution
            axes[idx].set_title(f"Qubit {idx}")
            axes[idx].plot(time, pulse[0], label="I")
            axes[idx].plot(time, pulse[1], label="Q")
            axes[idx].legend()
            axes[idx].minorticks_on()
            axes[idx].grid(which="both")
            axes[idx].set_ylabel("Amplitude")
            axes[idx].set_xlabel("Time (ns)")

        plt.tight_layout()
        # plt.savefig("test.png")
        return figure

    def add_gate(self, gate: HardwareGate):
        """Add gate to BusesExecution.

        Args:
            gate (HardwareGate): Hardware gate.
        """
        # Find if there is a BusExecution with the correct qubit_id, if not create one. If there is add the pulse.
