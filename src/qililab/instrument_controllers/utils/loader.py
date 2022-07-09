""" Instrument Modules Utility Loader Module."""

from dataclasses import dataclass
from typing import List

from qililab.instruments.instruments import Instruments
from qililab.instruments.utils.instrument_reference import InstrumentReference
from qililab.typings.enums import Category


@dataclass
class Loader:
    """Loads the Instruments supported types froom the Instrument References"""

    def _get_instrument_or_raise_error_when_not_found_or_not_supported_type(
        self, instruments: Instruments, category: Category, alias: str
    ):
        """get instrument or raise error when not found"""
        instrument = instruments.get_instrument(alias=alias, category=category)
        if instrument is None:
            raise ValueError(f"No instrument object found for category {category} and value {alias}.")

        return instrument

    def replace_modules_from_settings_with_instrument_objects(
        self,
        instruments: Instruments,
        instrument_references: List[InstrumentReference],
    ):
        """Replace dictionaries from settings into its respective instrument classes.

        Args:
            instruments (Instruments): Instruments loaded into the platform.
            instrument_references (List[InstrumentReference]): List of references to the instruments
            with its category and alias to be retrieved from the Instrument Factory.

        Returns:
            List[Instrument]: List of the Instruments that manages the Controller with its device driver assigned.
        """
        return [
            self._get_instrument_or_raise_error_when_not_found_or_not_supported_type(
                instruments=instruments, category=category[1], alias=alias[1]
            )
            for category, alias, _ in instrument_references
        ]
