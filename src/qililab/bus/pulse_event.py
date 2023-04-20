"""PulseEvent class."""
from __future__ import annotations

from dataclasses import dataclass, field

from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.constants import PULSEEVENT
from qililab.pulse.pulse import Pulse
from qililab.utils.waveforms import Waveforms


@dataclass
class PulseEvent:
    """Object representing a Pulse starting at a certain time."""

    pulse: PulseOperation
    start_time: int
    end_time: int

    @property
    def duration(self) -> int:
        return self.pulse.duration

    @property
    def frequency(self) -> float:
        return self.pulse.frequency

    def modulated_waveforms(self, resolution: float = 1.0) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        return self.pulse.modulated_waveforms(resolution=resolution, start_time=self.start_time)

    def __lt__(self, other: PulseEvent):
        """Returns True if and only if self.start_time is less than other.start_time

        Args:
            other (PulseEvent): PulseEvent to compare.

        Returns:
            bool: Comparison evaluation.
        """
        return self.start_time < other.start_time
