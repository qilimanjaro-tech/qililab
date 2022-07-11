"""Execution class."""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qiboconnection.api import API

from qililab.constants import GALADRIEL_DEVICE_ID
from qililab.execution.buses_execution import BusesExecution
from qililab.platform import Platform
from qililab.result import Result
from qililab.utils import LivePlot


@dataclass
class Execution:
    """Execution class."""

    buses_execution: BusesExecution
    platform: Platform
    connection: API | None
    device_id: int | None = GALADRIEL_DEVICE_ID

    def __enter__(self):
        """Code executed when starting a with statement."""
        if self.connection is not None:
            self.connection.block_device_id(device_id=self.device_id)
        self.connect()
        self.setup()
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        """Code executed when stopping a with statement."""
        if self.connection is not None:
            self.connection.release_device(device_id=self.device_id)
        self.close()

    def connect(self):
        """Connect to the instruments."""
        self.platform.connect()

    def setup(self):
        """Setup instruments with experiment settings."""
        self.buses_execution.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.buses_execution.start()

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

    def close(self):
        """Close connection to the instruments."""
        self.platform.close()

    def draw(self, resolution: float, idx: int = 0):
        """Save figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.buses_execution.draw(resolution=resolution, idx=idx)

    @property
    def num_sequences(self):
        """Execution 'num_sequences' property.

        Returns:
            int: Number of sequences played.
        """
        return self.buses_execution.num_sequences
