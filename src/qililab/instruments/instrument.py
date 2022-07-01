"""Instrument class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type, get_type_hints

from qililab.constants import YAML
from qililab.platform import BusElement
from qililab.settings import Settings
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
    class InstrumentSettings(Settings):
        """Contains the settings of an instrument.

        Args:
            firmware (str): Firmware version installed on the instrument.
        """

        firmware: str

    settings: InstrumentSettings  # a subtype of settings must be specified by the subclass

    def __init__(self, settings: dict):
        """Cast the settings to its corresponding class."""
        settings_class: Type[self.InstrumentSettings] = get_type_hints(self).get(YAML.SETTINGS)  # type: ignore
        self.settings = settings_class(**settings)

    def set_parameter(self, parameter: Parameter | str, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        if isinstance(parameter, Parameter):
            parameter = parameter.value
        self.settings.set_parameter(name=parameter, value=value)
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
