"""SystemControl class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Type, get_type_hints

from qililab.platform.components import BusElement
from qililab.pulse import PulseSequence
from qililab.result import Result
from qililab.settings import Settings
from qililab.typings import BusElementName


class SystemControl(BusElement, ABC):
    """SystemControl class."""

    @dataclass
    class SystemControlSettings(Settings):
        """SystemControlSettings class."""

        subcategory: BusElementName

    settings: SystemControlSettings

    def __init__(self, settings: dict):
        settings_class: Type[self.SystemControlSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings)

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
