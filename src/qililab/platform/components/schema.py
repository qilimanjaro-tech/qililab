"""Schema class"""
from typing import List

from qililab.chip import Chip
from qililab.constants import RUNCARD
from qililab.instruments import Instrument, InstrumentFactory, Instruments
from qililab.platform.components.bus import Bus
from qililab.platform.components.buses import Buses
from qililab.typings import SchemaDrawOptions


class Schema:
    """Class representing the schema of the platform.

    Args:
        settings (SchemaSettings): Settings that define the schema of the platform.
    """

    def __init__(self, buses: List[dict], instruments: List[dict], chip: dict):
        """Cast each list element to its corresponding bus class and instantiate class Buses."""
        self.instruments = Instruments(elements=self._load_instruments(instruments_dict=instruments))
        self.chip = Chip(**chip)
        self.buses = Buses(elements=[Bus(settings=bus, instruments=self.instruments, chip=self.chip) for bus in buses])

    def __str__(self):
        """String representation of the schema."""
        return "\n".join(str(bus) for bus in self.buses)

    def _load_instruments(self, instruments_dict: List[dict]) -> List[Instrument]:
        """Instantiate all instrument classes from their respective dictionaries.

        Args:
            instruments_dict (List[dict]): List of dictionaries containing the settings of each instrument.

        Returns:
            List[Instrument]: List of instantiated instrument classes.
        """
        return [
            InstrumentFactory.get(instrument.pop(RUNCARD.NAME))(settings=instrument) for instrument in instruments_dict
        ]

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return {"chip": self.chip.to_dict(), "instruments": self.instruments.to_dict(), "buses": self.buses.to_dict()}
