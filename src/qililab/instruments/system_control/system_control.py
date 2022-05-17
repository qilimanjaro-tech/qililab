"""SystemControl class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from qililab.pulse import Pulse
from qililab.settings import Settings
from qililab.typings import BusElement


class SystemControl(BusElement, ABC):
    """SystemControl class."""

    @dataclass
    class SystemControlSettings(Settings):
        """SystemControlSettings class."""

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
    def run(self, pulses: List[Pulse], nshots: int, loop_duration: int):
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
