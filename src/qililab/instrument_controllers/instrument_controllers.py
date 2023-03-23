"""Instrument Controllers class"""
from dataclasses import dataclass
from typing import List

import yaml

from qililab.instrument_controllers.instrument_controller import InstrumentController


@dataclass
class InstrumentControllers:
    """Instrument Controllers class."""

    elements: List[InstrumentController]

    def get_instrument_controller(self, alias: str | None = None):
        """Get instrument controller given an id_ and category"""
        for instrument in self.elements:
            if instrument.alias == alias:
                return instrument
        raise ValueError(f"Could not find instrument controller with alias {alias}")

    def connect(self):
        """Connect to all instrument controllers."""
        for instrument_controller in self.elements:
            instrument_controller.connect()

    def initial_setup(self):
        """Set the initial setup of the instruments"""
        for instrument_controller in self.elements:
            instrument_controller.initial_setup()

    def turn_on_instruments(self):
        """Turn on the instrument"""
        for instrument_controller in self.elements:
            instrument_controller.turn_on()

    def turn_off_instruments(self):
        """Turn off the instrument"""
        for instrument_controller in self.elements:
            instrument_controller.turn_off()

    def disconnect(self):
        """Disconnect from all instrument controllers."""
        for instrument_controller in self.elements:
            instrument_controller.disconnect()

    def to_dict(self):
        """Return a dict representation of the Instrument Controllers class."""
        return [instrument_controller.to_dict() for instrument_controller in self.elements]

    def __str__(self) -> str:
        """
        Returns:
            str: String representation of the Instrument Controllers class.
        """
        return str(yaml.dump(self.to_dict(), sort_keys=False))
