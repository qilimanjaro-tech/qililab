"""SystemControl class."""
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path

from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseSequence
from qililab.result import Result
from qililab.typings import BusElementName


class SystemControl(Instrument):
    """SystemControl class."""

    @dataclass
    class SystemControlSettings(Instrument.InstrumentSettings):
        """SystemControlSettings class."""

        subcategory: BusElementName

    settings: SystemControlSettings

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path) -> Result:
        """Run the given pulse sequence."""

    @property
    def id_(self):
        """SystemControl 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def category(self):
        """SystemControl 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    @abstractmethod
    def frequency(self) -> float:
        """SystemControl 'frequency' property."""
