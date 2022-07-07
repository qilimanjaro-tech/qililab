"""SystemControl class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Type, get_type_hints

from qililab.platform.components import BusElement
from qililab.pulse import PulseSequence
from qililab.result import Result
from qililab.settings import DDBBElement
from qililab.typings import SystemControlSubcategory


class SystemControl(BusElement, ABC):
    """SystemControl class."""

    @dataclass
    class SystemControlSettings(DDBBElement):
        """SystemControlSettings class."""

        subcategory: SystemControlSubcategory

    settings: SystemControlSettings

    def __init__(self, settings: dict):
        settings_class: Type[self.SystemControlSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings)

    @abstractmethod
    def start(self):
        """Start instrument."""

    @abstractmethod
    def setup(self, frequencies: List[float]):
        """Set instrument settings."""

    @abstractmethod
    def run(
        self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path
    ) -> List[Result] | None:
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
    def subcategory(self):
        """SystemControl 'subcategory' property.

        Returns:
            str: settings.subcategory.
        """
        return self.settings.subcategory

    @property
    @abstractmethod
    def awg_frequency(self) -> float:
        """SystemControl 'awg_frequency' property."""

    @property
    @abstractmethod
    def frequency(self) -> float:
        """SystemControl 'frequency' property."""

    @property
    @abstractmethod
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.

        Returns:
            int: Delay (in ns) between the readout pulse and the acquisition.
        """
