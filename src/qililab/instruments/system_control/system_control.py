"""SystemControl class."""
from abc import ABC, abstractmethod

from qililab.pulse import PulseSequence
from qililab.result import Result
from qililab.settings import Settings
from qililab.typings import BusElement, BusElementName
from qililab.utils import nested_dataclass


class SystemControl(BusElement, ABC):
    """SystemControl class."""

    @nested_dataclass
    class SystemControlSettings(Settings):
        """SystemControlSettings class."""

        subcategory: BusElementName

    settings: SystemControlSettings

    @abstractmethod
    def connect(self):
        """Connect to the instruments."""

    @abstractmethod
    def setup(self):
        """Setup instruments."""

    @abstractmethod
    def start(self):
        """Start/Turn on the instruments."""

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int) -> Result:
        """Run the given pulse sequence."""

    @abstractmethod
    def close(self):
        """Close connection to the instruments."""

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
