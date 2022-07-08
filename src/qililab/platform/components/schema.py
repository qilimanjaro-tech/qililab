"""Schema class"""
from typing import List

from qililab.chip import Chip
from qililab.constants import RUNCARD, SCHEMA
from qililab.instrument_controllers.instrument_controller import InstrumentController
from qililab.instrument_controllers.instrument_controllers import InstrumentControllers
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils import InstrumentFactory
from qililab.platform.components.bus import Bus
from qililab.platform.components.buses import Buses


class Schema:
    """Class representing the schema of the platform."""

    def __init__(self, buses: List[dict], instruments: List[dict], chip: dict, instrument_controllers: List[dict]):
        """Cast each list element to its corresponding bus class and instantiate class Buses."""
        self.instruments = Instruments(elements=self._load_instruments(instruments_dict=instruments))
        self.chip = Chip(**chip)
        self.buses = Buses(elements=[Bus(settings=bus, instruments=self.instruments, chip=self.chip) for bus in buses])
        self.instrument_controllers = InstrumentControllers(
            elements=self._load_instrument_controllers(instrument_controllers_dict=instrument_controllers)
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
            SCHEMA.CHIP: self.chip.to_dict(),
            SCHEMA.INSTRUMENTS: self.instruments.to_dict(),
            SCHEMA.BUSES: self.buses.to_dict(),
            SCHEMA.INSTRUMENT_CONTROLLERS: self.instrument_controllers.to_dict(),
        }
