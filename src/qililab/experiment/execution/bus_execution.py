"""BusExecution class."""
from dataclasses import dataclass

from qililab.experiment.pulse.pulse_sequence import PulseSequence
from qililab.platform import Bus


class BusExecution:
    """BusExecution class."""

    @dataclass
    class BusExecutionSettings:
        """Settings of the BusExecution class."""

        bus: Bus
        pulse_sequence: PulseSequence.PulseSequenceSettings

    settings: BusExecutionSettings

    def __init__(self, settings: dict):
        self.settings = self.BusExecutionSettings(**settings)

    @property
    def bus(self):
        """BusExecution 'bus' property.

        Returns:
            Bus: settings.bus
        """
        return self.settings.bus

    @property
    def pulse_sequence(self):
        """BusExecution 'pulse_sequence' property.

        Returns:
            PulseSequence: settings.pulse_sequence
        """
        return self.settings.pulse_sequence
