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

    def waveforms(self, resolution: float = 1.0):
        """PulseSequence 'waveforms' property.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Tuple[List[float], List[float]]: Dictionary containing the I, Q waveforms for a specific qubit.
        """
        waveforms_i: List[float] = []
        waveforms_q: List[float] = []
        time = 0
        for pulse in self.pulses:
            wait_time = round((pulse.start - time) / resolution)
            waveforms_i += [0 for _ in range(wait_time)]
            waveforms_q += [0 for _ in range(wait_time)]
            time += pulse.start
            waveform_i, waveform_q = pulse.modulated_waveforms(resolution=resolution)
            waveforms_i += waveform_i.tolist()
            waveforms_q += waveform_q.tolist()
            time += pulse.duration

        return waveforms_i, waveforms_q

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
