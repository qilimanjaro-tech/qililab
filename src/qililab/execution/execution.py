"""Execution class."""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qililab.execution.buses_execution import BusesExecution
from qililab.platform import Platform
from qililab.result import Result
from qililab.typings.execution import ExecutionOptions
from qililab.utils import LivePlot


@dataclass
class Execution:
    """Execution class."""

    buses_execution: BusesExecution
    platform: Platform
    options: ExecutionOptions

    def __enter__(self):
        """Code executed when starting a with statement."""
        if self.options.automatic_connect_to_instruments:
            self.connect()
        if self.options.set_initial_setup:
            self.set_initial_setup()
        if self.options.automatic_turn_on_instruments:
            self.turn_on_instruments()

    def __exit__(self, exc_type, exc_value, traceback):
        """Code executed when stopping a with statement."""
        if self.options.automatic_turn_off_instruments:
            self.turn_off_instruments()
        if self.options.automatic_disconnect_to_instruments:
            self.disconnect()

    def connect(self):
        """Connect to the instruments."""
        self.platform.connect()

    def set_initial_setup(self):
        """Setup instruments with experiment settings."""
        self.platform.set_initial_setup()

    def turn_off_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_off_instruments()

    def turn_on_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_on_instruments()

    def run(
        self, nshots: int, repetition_duration: int, software_average: int, plot: LivePlot | None, path: Path
    ) -> List[Result]:
        """Run the given pulse sequence."""
        return self.buses_execution.run(
            nshots=nshots,
            repetition_duration=repetition_duration,
            software_average=software_average,
            plot=plot,
            path=path,
        )

    def disconnect(self):
        """Disconnect from the instruments."""
        self.platform.disconnect()

    def draw(self, resolution: float, idx: int = 0):
        """Save figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.buses_execution.draw(resolution=resolution, idx=idx)

    @property
    def num_schedules(self):
        """Execution 'num_schedules' property.

        Returns:
            int: Number of sequences played.
        """
        return self.buses_execution.num_schedules
