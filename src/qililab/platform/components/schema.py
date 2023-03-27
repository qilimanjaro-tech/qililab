"""Schema class"""
from typing import List

from qililab.chip import Chip
from qililab.constants import RUNCARD, SCHEMA
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils import InstrumentFactory
from qililab.platform.components import Bus, Buses


class Schema:
    """Class representing the schema of the platform."""

    def __init__(self, buses: List[dict], instruments: List[dict], chip: dict, instrument_controllers: List[dict]):
        """Cast each list element to its corresponding bus class and instantiate class Buses."""
        self.instruments = (
            Instruments(elements=self._load_instruments(instruments_dict=instruments))
            if instruments is not None
            else None
        )
        self.chip = Chip(**chip) if chip is not None else None
        self.buses = (
            Buses(elements=[Bus(settings=bus, platform_instruments=self.instruments, chip=self.chip) for bus in buses])
            if buses is not None
            else None
        )
        self.instrument_controllers = (
            InstrumentControllers(
                elements=self._load_instrument_controllers(instrument_controllers_dict=instrument_controllers)
            )
            if instrument_controllers is not None
            else None
        )

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

    def _load_instrument_controllers(self, instrument_controllers_dict: List[dict]) -> List[InstrumentController]:
        """Instantiate all instrument controller classes from their respective dictionaries.

        Args:
            instrument_controllers_dict (List[dict]): List of dictionaries containing
            the settings of each instrument controller.

        Returns:
            List[InstrumentController]: List of instantiated instrument controller classes.
        """
        return [
            InstrumentControllerFactory.get(instrument_controller.pop(RUNCARD.NAME))(
                settings=instrument_controller, loaded_instruments=self.instruments
            )
            for instrument_controller in instrument_controllers_dict
        ]

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return {
            SCHEMA.CHIP: self.chip.to_dict() if self.chip is not None else None,
            SCHEMA.INSTRUMENTS: self.instruments.to_dict() if self.instruments is not None else None,
            SCHEMA.BUSES: self.buses.to_dict() if self.buses is not None else None,
            SCHEMA.INSTRUMENT_CONTROLLERS: self.instrument_controllers.to_dict()
            if self.instrument_controllers is not None
            else None,
        }
