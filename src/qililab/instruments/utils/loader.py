# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Instrument Modules Utility Loader Module."""

from dataclasses import dataclass

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
        instruments: Instruments,
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
