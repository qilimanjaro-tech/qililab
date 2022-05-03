"""Experiment class."""
import matplotlib.pyplot as plt

from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform


class Experiment:
    """Execution class"""

    platform: Platform
    execution: Execution

    def __init__(self, experiment_name: str, platform_name: str):
        self.platform = PLATFORM_MANAGER_DB.build(platform_name=platform_name)
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, experiment_name=experiment_name)

    def execute(self):
        """Run execution."""
        return self.execution.execute()

    @property
    def pulses(self):
        """Experiment 'pulses' property.

        Returns:
            Dict[int, np.ndarray]: Dictionary containing a list of the I/Q amplitudes of the control and readout
            pulses applied on each qubit.
        """
        return self.execution.pulses

    def draw(self):
        """Save figure with the waveforms sent to each bus."""
        num_qubits = self.platform.num_qubits
        _, axes = plt.subplots(num_qubits, 1)
        if num_qubits == 1:
            axes = [axes]  # make axes subscriptable
        for idx, pulse in self.pulses.items():
            axes[idx].set_title(f"Qubit {idx}")
            axes[idx].plot(pulse[0])  # I waveform
            axes[idx].plot(pulse[1])  # Q waveform

        plt.tight_layout()
        plt.savefig("test.png")
        plt.show()
