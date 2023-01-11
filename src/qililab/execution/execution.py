"""Execution class."""
from dataclasses import dataclass
from pathlib import Path
from qililab.execution import execution_manager

from qililab.execution.execution_manager import ExecutionManager
from qililab.platform import Platform
from qililab.result import Result
from qililab.typings.execution import ExecutionOptions
from qililab.utils import LivePlot


@dataclass
class Execution:
    """Execution class."""

    execution_manager: ExecutionManager
    platform: Platform
    options: ExecutionOptions

    def __enter__(self):
        """Code executed when starting a with statement."""
        self.connect_setup_and_turn_on_if_needed()

    def connect_setup_and_turn_on_if_needed(self):
        """connect, setup, and turn on if needed."""
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

    def generate_program_and_upload(
        self, schedule_index_to_load: int, nshots: int, repetition_duration: int, path: Path
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            schedule_index_to_load (int): specific schedule to load
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            path (Path): path to save the program to upload
        """
        return self.execution_manager.generate_program_and_upload(
            schedule_index_to_load=schedule_index_to_load,
            nshots=nshots,
            repetition_duration=repetition_duration,
            path=path,
        )
        
    def setup(self) -> None:
        """This calls the setup of the execution manager"""
        self.execution_manager.setup()

    def run(self, plot: LivePlot | None, path: Path) -> Result | None:
        """Run the given pulse sequence."""
        return self.execution_manager.run(plot=plot, path=path)

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
        return self.execution_manager.draw(resolution=resolution, idx=idx)

    @property
    def num_schedules(self):
        """Execution 'num_schedules' property.

        Returns:
            int: Number of sequences played.
        """
        return self.execution_manager.num_schedules
