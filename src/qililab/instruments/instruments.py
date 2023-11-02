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

"""Instruments class"""
import io
from dataclasses import dataclass

from ruamel.yaml import YAML

from qililab.instruments.instrument import Instrument


@dataclass
class Instruments:
    """Instruments class."""

    elements: list[Instrument]

    def get_instrument(self, alias: str | None = None):
        """Get element given an alias."""
        return next((element for element in self.elements if element.alias == alias), None)

    def to_dict(self):
        """Return a dict representation of the Instruments class."""
        return [instrument.to_dict() for instrument in self.elements]

    def __str__(self) -> str:
        """
        Returns:
            str: String representation of the Instruments class.
        """
        return str(YAML().dump(self._short_dict(), io.BytesIO()))

    def _short_dict(self):
        """Return a dict representation of the Instruments class discarding all static elements."""
        return [instrument.short_dict() for instrument in self.elements]
