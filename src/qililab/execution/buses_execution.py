"""BusesExecution class."""
from dataclasses import dataclass, field
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from qililab.execution.bus_execution import BusExecution
from qililab.result import Result


@dataclass
class BusesExecution:
    """BusesExecution class."""

    num_sequences: int
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

    def run(self, nshots: int, repetition_duration: int):
        """Run the given pulse sequence."""
        results: List[Result] = []
        for idx in range(self.num_sequences):
            for bus in self.buses:
                result = bus.run(nshots=nshots, repetition_duration=repetition_duration, idx=idx)
                if result is not None:
                    results.append(result)
                    # print(result.probabilities()[0])
        return results

    def close(self):
        """Close connection to the instruments."""
        for bus in self.buses:
            bus.close()

    def waveforms(self, resolution: float = 1.0):
        """Get pulses of each bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Dict[int, np.ndarray]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on each bus.
        """
        return {bus.id_: np.array(bus.waveforms(resolution=resolution)) for bus in self.buses}

    def draw(self, resolution: float):
        """Save figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        figure, axes = plt.subplots(nrows=len(self.buses), ncols=1, sharex=True)
        if len(self.buses) == 1:
            axes = [axes]  # make axes subscriptable
        for bus_idx, pulse in self.waveforms(resolution=resolution).items():
            time = np.arange(len(pulse[0])) * resolution
            axes[bus_idx].set_title(f"Bus {bus_idx}")
            axes[bus_idx].plot(time, pulse[0], label="I")
            axes[bus_idx].plot(time, pulse[1], label="Q")
            axes[bus_idx].legend()
            axes[bus_idx].minorticks_on()
            axes[bus_idx].grid(which="both")
            axes[bus_idx].set_ylabel("Amplitude")
            axes[bus_idx].set_xlabel("Time (ns)")

        plt.tight_layout()
        # plt.savefig("test.png")
        return figure
