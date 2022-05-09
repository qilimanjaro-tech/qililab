"""HardwareExperiment class."""
from dataclasses import asdict, dataclass

from qibo.core.circuit import Circuit

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.pulse import PulseSequence


class Experiment:
    """HardwareExperiment class"""

    @dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 4096
        software_average: int = 10
        repetition_duration: int = 20000

    platform: Platform
    execution: Execution
    settings: ExperimentSettings

    def __init__(
        self, sequence: Circuit | PulseSequence, platform_name: str = DEFAULT_PLATFORM_NAME, settings: dict = None
    ):
        self.settings = self.ExperimentSettings() if settings is None else self.ExperimentSettings(**settings)
        self.platform = PLATFORM_MANAGER_DB.build(
            platform_name=platform_name, experiment_settings=asdict(self.settings)
        )
        if isinstance(sequence, PulseSequence):
            self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequence=sequence)

    def execute(self):
        """Run execution."""
        return self.execution.execute()

    def draw(self, resolution: float = 1.0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution)
