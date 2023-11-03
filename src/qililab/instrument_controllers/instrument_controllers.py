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

"""Instrument Controllers class"""
import io
from dataclasses import dataclass

from ruamel.yaml import YAML

from qililab.instrument_controllers.instrument_controller import InstrumentController


@dataclass
class InstrumentControllers:
    """Instrument Controllers class."""

    elements: list[InstrumentController]

    def get_instrument_controller(self, alias: str | None = None):
        """Get instrument controller given an id and category"""
        return next((instrument for instrument in self.elements if instrument.alias == alias), None)

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
        return str(YAML().dump(self.to_dict(), io.BytesIO()))
