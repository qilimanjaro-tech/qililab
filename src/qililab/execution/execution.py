"""Execution class."""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qililab.execution.execution_manager import ExecutionManager
from qililab.platform import Platform
from qililab.result import Result
from qililab.utils import LivePlot, Loop


@dataclass
class Execution:
    """Execution class."""

    execution_manager: ExecutionManager
    platform: Platform

    def turn_on_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_on_instruments()

    def turn_off_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_off_instruments()

    def generate_program_and_upload(
        self, idx: int, nshots: int, repetition_duration: int, path: Path, hw_loop: Loop | None
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            schedule_index_to_load (int): specific schedule to load
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            path (Path): path to save the program to upload
        """
        return self.execution_manager.generate_program_and_upload(
            idx=idx, nshots=nshots, repetition_duration=repetition_duration, path=path, hw_loop=hw_loop
        )

    def run(self, plot: LivePlot | None, path: Path) -> Result | None:
        """Run the given pulse sequence."""
        return self.execution_manager.run(plot=plot, path=path)

    def draw(self, resolution: float, idx: int = 0):
        """Save figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution_manager.draw(resolution=resolution, idx=idx)

    @property
    def num_schedules(self):
        """Execution 'num_schedules' property.

        Returns:
            int: Number of sequences played.
        """
        return self.execution_manager.num_schedules
