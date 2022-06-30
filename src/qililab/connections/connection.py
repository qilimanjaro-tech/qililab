"""Instrument class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type, get_type_hints

from qililab.constants import YAML
from qililab.settings import Settings


class Connection(ABC):
    """Abstract base class declaring the necessary attributes and methods for a connection."""

    @dataclass
    class ConnectionSettings(Settings):
        """Contains the settings of an instrument."""

        address: str

    settings: ConnectionSettings  # a subtype of settings must be specified by the subclass

    def __init__(self, settings: dict):
        settings_class: Type[self.ConnectionSettings] = get_type_hints(YAML.SETTINGS)  # type: ignore
        self.settings = settings_class(**settings)

    @abstractmethod
    def connect(self):
        """Establish connection."""
        pass

    @abstractmethod
    def close(self):
        """Close connection."""
        pass
