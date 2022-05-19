"""BusPulses class."""
from dataclasses import dataclass, field
from typing import List

from qililab.pulse.pulse import Pulse


@dataclass
class PulseSequence:
    """Container of Pulse objects addressed to the same bus."""

    qubit_ids: List[int]
    pulses: List[Pulse] = field(default_factory=list)

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        if pulse.qubit_ids != self.qubit_ids:
            raise ValueError("All Pulse objects inside a BusPulses class should contain the same qubit_ids.")
        if pulse.name != self.pulses[0].name:
            raise ValueError(
                "All Pulse objects inside a BusPulses class should have the same type (Pulse or ReadoutPulse)."
            )
        self.pulses.append(pulse)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.pulses.__iter__()

    def waveforms(self, frequency: float, resolution: float = 1.0):
        """PulseSequence 'waveforms' property.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Tuple[List[float], List[float]]: Tuple containing the I, Q waveforms for a specific qubit.
        """
        waveforms_i: List[float] = []
        waveforms_q: List[float] = []
        time = 0
        for pulse in self.pulses:
            if pulse.start is None:
                raise ValueError("Start time of pulse is not defined.")
            wait_time = round((pulse.start - time) / resolution)
            waveforms_i += [0] * wait_time
            waveforms_q += [0] * wait_time
            time += pulse.start
            waveform_i, waveform_q = pulse.modulated_waveforms(frequency=frequency, resolution=resolution)
            waveforms_i += waveform_i.tolist()
            waveforms_q += waveform_q.tolist()
            time += pulse.duration

        return waveforms_i, waveforms_q
