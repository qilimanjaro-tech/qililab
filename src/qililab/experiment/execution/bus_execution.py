"""BusExecution class."""
from dataclasses import dataclass

from qililab.experiment.pulse.pulse_sequence import PulseSequence
from qililab.platform import Bus


@dataclass
class BusExecution:
    """BusExecution class."""

    @dataclass
    class BusExecutionSettings:
        """Settings of the BusExecution class."""

        bus: Bus
        pulse_sequence: PulseSequence.PulseSequenceSettings
