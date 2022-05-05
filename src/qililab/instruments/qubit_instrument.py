"""QubitControl class."""
from abc import abstractmethod
from typing import ClassVar

from qililab.instruments.instrument import Instrument
from qililab.pulse.pulse_sequence import PulseSequence
from qililab.settings import ExperimentSettings
from qililab.typings import BusElement
from qililab.utils import nested_dataclass


class QubitInstrument(Instrument, BusElement):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @nested_dataclass
    class QubitInstrumentSettings(Instrument.InstrumentSettings):
        """Contains the settings of a QubitInstrument.

        Args:
            hardware_average (ClassVar[int]): Hardware average. Number of shots used when executing a sequence.
            software_average (ClassVar[int]): Software average.
            repetition_duration (ClassVar[int]): Duration (ns) of the whole program.
            delay_between_pulses (ClassVar[int]): Delay (ns) between two consecutive pulses.
        """

        hardware_average: ClassVar[int]
        software_average: ClassVar[int]
        repetition_duration: ClassVar[int]
        delay_between_pulses: ClassVar[int]

    settings: QubitInstrumentSettings

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence):
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """

    @classmethod
    def general_setup(
        cls, settings: ExperimentSettings
    ):  # TODO: Use PlatformSetupBuilder to build Platform with this ExperimentSettings
        """Setup generic qubit instrument settings.

        Args:
            settings (GenericQubitInstrumentSettings): Generic QubitInstrument settings.
        """
        cls.QubitInstrumentSettings.hardware_average = settings.hardware_average
        cls.QubitInstrumentSettings.software_average = settings.software_average
        cls.QubitInstrumentSettings.delay_between_pulses = settings.delay_between_pulses
        cls.QubitInstrumentSettings.repetition_duration = settings.repetition_duration

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
