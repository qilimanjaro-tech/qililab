"""Instrument Controllers class"""
from dataclasses import dataclass
from typing import List

import yaml

from qililab.instrument_controllers.instrument_controller import InstrumentController


@dataclass
class InstrumentControllers:
    """Instrument Controllers class."""

    elements: List[InstrumentController]

    def connect(self):
        """Connect to all instrument controllers."""
        for instrument_controller in self.elements:
            instrument_controller.connect()

    def close(self):
        """Close all instrument controllers."""
        for instrument_controller in self.elements:
            instrument_controller.close()

    def to_dict(self):
        """Return a dict representation of the Instrument Controllers class."""
        return [instrument_controller.to_dict() for instrument_controller in self.elements]

    def __str__(self) -> str:
        """
        Returns:
            str: String representation of the Instrument Controllers class.
        """
        return str(yaml.dump(self.to_dict(), sort_keys=False))
