"""BusExecution class."""
from dataclasses import dataclass, field
from typing import List

from sympy import Q

from qililab.platform import Bus
from qililab.pulse import BusPulses, Pulse


@dataclass
class BusExecution:
    """BusExecution class."""

    bus: Bus
    pulse_sequences: List[BusPulses] = field(default_factory=list)

    def connect(self):
        """Connect to the instruments."""
        self.bus.connect()

    def setup(self):
        """Setup instruments."""
        self.bus.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.bus.start()

    def run(self, idx: int):
        """Run the given pulse sequence."""
        return self.bus.run(pulses=self.pulse_sequences[idx].pulses)

    def close(self):
        """Close connection to the instruments."""
        self.bus.close()

    def add_pulse(self, pulse: Pulse, idx: int):
        """Add pulse to the BusPulseSequence given by idx.

        Args:
            pulse (Pulse): Pulse object.
            idx (int): Index of the BusPulseSequence to add the pulse.
        """
        if idx > len(self.pulse_sequences):
            raise ValueError("Bad index value.")
        if idx == len(self.pulse_sequences):
            self.pulse_sequences.append(BusPulses(qubit_ids=pulse.qubit_ids, pulses=[pulse]))
        else:
            self.pulse_sequences[idx].add(pulse)

    def waveforms(self, resolution: float = 1.0):
        """Return pulses applied on this bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Tuple[List[float], List[float]]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on this bus.
        """
        waveforms_i, waveforms_q = [], []
        for pulse_sequence in self.pulse_sequences:
            waveform_i, waveform_q = pulse_sequence.waveforms(
                frequency=self.qubit_instrument.frequency, resolution=resolution
            )
            waveform_i += [0] * (self.qubit_instrument.repetition_duration - len(waveform_i))
            waveform_q += [0] * (self.qubit_instrument.repetition_duration - len(waveform_q))
            waveforms_i += waveform_i
            waveforms_q += waveform_q
        return waveforms_i, waveforms_q

    @property
    def qubit_ids(self):
        """BusExecution 'qubit_ids' property

        Returns:
            int: ID of the qubit connected to the bus.
        """
        return self.bus.qubit_ids

    @property
    def qubit_instrument(self):
        """BusExecution 'qubit_instrument' property.

        Returns:
            QubitInstrument: bus.qubit_instrument
        """
        return self.bus.qubit_instrument
