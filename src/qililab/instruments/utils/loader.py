""" Instrument Modules Utility Loader Module."""

from dataclasses import dataclass

from qililab.drivers.instruments import Instruments as NewInstruments
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils.instrument_reference import InstrumentReference


@dataclass
class Loader:
    """Loads the Instruments supported types froom the Instrument References"""

    def _get_instrument_or_raise_error_when_not_found_or_not_supported_type(self, instruments: Instruments, alias: str):
        """get instrument or raise error when not found"""
        instrument = instruments.get_instrument(alias=alias)
        if instrument is None:
            raise ValueError(f"No instrument object found for alias {alias}.")

        return instrument

    def replace_modules_from_settings_with_instrument_objects(
        self,
        instruments: Instruments | NewInstruments,
        instrument_references: list[InstrumentReference],
    ):
        """Replace dictionaries from settings into its respective instrument classes.

        Args:
            instruments (Instruments): Instruments loaded into the platform.
            instrument_references (list[InstrumentReference]): List of references to the instruments
            with its alias to be retrieved from the Instrument Factory.

        Returns:
            list[Instrument]: List of the Instruments that manages the Controller with its device driver assigned.
        """
        return [
            self._get_instrument_or_raise_error_when_not_found_or_not_supported_type(
                instruments=instruments, alias=alias[1]
            )
            for alias, _ in instrument_references
        ]
