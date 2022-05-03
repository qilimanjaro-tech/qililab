"""PulseSequence class."""
from dataclasses import dataclass
from typing import List

from qililab.pulse.pulse import Pulse


@dataclass
class PulseSequence:
    """Class containing a list of pulses used for control/readout of the qubit.

    Args:
        readout (bool): readout flag.
        pulses (List[Pulse]): List of pulses.
    """

    readout: bool
    qubit_id: int
    pulses: List[Pulse]

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        if pulse.readout != self.readout:
            raise ValueError("A single PulseSequence object cannot contain control and readout pulses.")
        if pulse.qubit_id != self.qubit_id:
            raise ValueError("A single PulseSequence object cannot contain pulses of different qubits.")
        self.pulses.append(pulse)

    @property
    def waveforms(self):
        """PulseSequence 'waveforms' property.

        Returns:
            Tuple[List[float], List[float]]: Dictionary containing the I, Q waveforms for a specific qubit.
        """
        waveforms_i: List[float] = []
        waveforms_q: List[float] = []
        time = 0
        for pulse in self.pulses:
            waveforms_i += [0 for _ in range(pulse.start - time)]
            waveforms_q += [0 for _ in range(pulse.start - time)]
            time += pulse.start
            waveform_i, waveform_q = pulse.modulated_waveforms
            waveforms_i += waveform_i.tolist()
            waveforms_q += waveform_q.tolist()
            time += pulse.duration

        return waveforms_i, waveforms_q

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
