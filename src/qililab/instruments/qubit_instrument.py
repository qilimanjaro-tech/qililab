"""QubitControl class."""
from abc import abstractmethod

from qililab.instruments.instrument import Instrument
from qililab.pulse.pulse_sequence import PulseSequence
from qililab.typings import BusElement
from qililab.utils import nested_dataclass


class QubitInstrument(Instrument, BusElement):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @nested_dataclass(kw_only=True)
    class QubitInstrumentSettings(Instrument.InstrumentSettings):
        """Contains the settings of a QubitInstrument.

        Args:
            hardware_average (int): Hardware average. Number of shots used when executing a sequence.
            software_average (int): Software average.
            repetition_duration (int): Duration (ns) of the whole program.
            delay_between_pulses (int): Delay (ns) between two consecutive pulses.
        """

        hardware_average: int = 4096
        software_average: int = 10
        repetition_duration: int = 200000
        delay_between_pulses: int = 0

    settings: QubitInstrumentSettings

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence):
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """

    @property
    def hardware_average(self):
        """QbloxPulsar 'hardware_average' property.

        Returns:
            int: settings.hardware_average.
        """
        return self.QubitInstrumentSettings.hardware_average

    @property
    def software_average(self):
        """QbloxPulsar 'software_average' property.

        Returns:
            int: settings.software_average.
        """
        return self.settings.software_average

    @property
    def delay_between_pulses(self):
        """QbloxPulsar 'delay_between_pulses' property.

        Returns:
            int: settings.delay_between_pulses.
        """
        return self.settings.delay_between_pulses

    @property
    def repetition_duration(self):
        """QbloxPulsar 'repetition_duration' property.

        Returns:
            int: settings.repetition_duration.
        """
        return self.settings.repetition_duration
