"""PulseBuilder class"""
from typing import Dict, List

from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_sequence import PulseSequence
from qililab.utils import Singleton


class PulseBuilder(metaclass=Singleton):
    """Builder of PulseSequence objects."""

    def build(self, pulses: List[Pulse]):
        """Build PulseSequence objects.

        Returns:
            Dict[int, PulseSequence]: Dictionary containing all control/readout PulseSequence for each different qubit.
        """
        control_pulses, readout_pulses = self._classify_pulses(pulses=pulses)

        control_pulse_sequences = self._load_pulse_sequences(pulses=control_pulses)
        readout_pulse_sequences = self._load_pulse_sequences(pulses=readout_pulses)

        return control_pulse_sequences, readout_pulse_sequences

    def _classify_pulses(self, pulses: List[Pulse]):
        """Cast control and readout pulse settings into Pulse objects.

        Args:
            pulse_sequence_settings (List[dict]): List of pulse settings.

        Returns:
            Tuple[List, List]: List of control and readout Pulse objects.
        """
        control_pulses = []
        readout_pulses = []
        for pulse in pulses:
            if pulse.readout is False:
                control_pulses.append(pulse)
            elif pulse.readout is True:
                readout_pulses.append(pulse)

        return control_pulses, readout_pulses

    def _load_pulse_sequences(self, pulses: List[Pulse]):
        """Generate a PulseSequence class for each different qubit targetted by the given pulses.

        Args:
            pulses (List[Pulse]): List of Pulse objects.

        Returns:
            Dict[int, PulseSequence]: Dictionary containing a PulseSequence for each different qubit.
        """
        pulse_sequences: Dict[int, PulseSequence] = {}
        for pulse in pulses:
            if pulse.qubit_id not in pulse_sequences:
                pulse_sequences[pulse.qubit_id] = PulseSequence(readout=pulse.readout, pulses=[pulse])
                continue
            pulse_sequences[pulse.qubit_id].add(pulse=pulse)
        return pulse_sequences
