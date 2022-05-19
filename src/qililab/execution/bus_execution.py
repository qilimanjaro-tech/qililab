"""BusExecution class."""
from dataclasses import dataclass, field
from typing import List

from qililab.platform import Bus
from qililab.pulse import Pulse, PulseSequence


@dataclass
class BusExecution:
    """BusExecution class."""

    bus: Bus
    pulse_sequences: List[PulseSequence] = field(default_factory=list)

    def connect(self):
        """Connect to the instruments."""
        self.bus.connect()

    def setup(self):
        """Setup instruments."""
        self.bus.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.bus.start()

    def run(self, nshots: int, loop_duration: int, idx: int):
        """Run the given pulse sequence."""
        return self.bus.run(pulse_sequence=self.pulse_sequences[idx], nshots=nshots, loop_duration=loop_duration)

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
            self.pulse_sequences.append(PulseSequence(qubit_ids=pulse.qubit_ids, pulses=[pulse]))
        else:
            self.pulse_sequences[idx].add(pulse)

    def waveforms(self, loop_duration: int, resolution: float = 1.0):
        """Return pulses applied on this bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Tuple[List[float], List[float]]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on this bus.
        """
        waveforms_i, waveforms_q = [], []
        for pulse_sequence in self.pulse_sequences:
            waveform_i, waveform_q = pulse_sequence.waveforms(
                frequency=self.system_control.frequency, resolution=resolution
            )
            waveforms_i += waveform_i
            waveforms_q += waveform_q
            wait_time = round(loop_duration / resolution - len(waveform_i))
            waveforms_i += [0] * wait_time
            waveforms_q += [0] * wait_time
        return waveforms_i, waveforms_q

    @property
    def qubit_ids(self):
        """BusExecution 'qubit_ids' property

        Returns:
            int: ID of the qubit connected to the bus.
        """
        return self.bus.qubit_ids

    @property
    def system_control(self):
        """BusExecution 'system_control' property.

        Returns:
            QubitInstrument: bus.system_control
        """
        return self.bus.system_control
