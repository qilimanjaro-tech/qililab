"""Instrument class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type, get_type_hints

from qililab.constants import RUNCARD
from qililab.platform import BusElement
from qililab.settings import DDBBElement
from qililab.typings import InstrumentName, Parameter


class Instrument(BusElement, ABC):
    """Abstract base class declaring the necessary attributes
    and methods for the instruments connected via TCP/IP.

    Args:
        device (Device): Class used for connecting to the instrument.
        settings (Settings): Class containing the settings of the instrument.
    """

    name: InstrumentName

    @dataclass
    class InstrumentSettings(DDBBElement):
        """Contains the settings of an instrument.

        Args:
            firmware (str): Firmware version installed on the instrument.
        """

        firmware: str

    settings: InstrumentSettings  # a subtype of settings must be specified by the subclass

    def __init__(self, settings: dict):
        """Cast the settings to its corresponding class."""
        settings_class: Type[self.InstrumentSettings] = get_type_hints(self).get(RUNCARD.SETTINGS)  # type: ignore
        self.settings = settings_class(**settings)

    def set_parameter(self, parameter: Parameter, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        self.settings.set_parameter(parameter=parameter, value=value)
        self.setup()

    @abstractmethod
    def setup(self):
        """Set instrument settings."""

    @property
    def id_(self):
        """Instrument 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def alias(self):
        """Instrument 'alias' property.

        Returns:
            int: settings.alias.
        """
        return self.settings.alias

    @property
    def category(self):
        """Instrument 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def firmware(self):
        """Instrument 'firmware' property.

        Returns:
            str: settings.firmware.
        """
        return self.settings.firmware

    def __str__(self):
        """String representation of an instrument."""
        return f"{self.alias}" if self.alias is not None else f"{self.category}_{self.id_}"
