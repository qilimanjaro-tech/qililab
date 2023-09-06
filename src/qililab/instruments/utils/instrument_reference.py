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

""" Instrument Reference class. """

from dataclasses import dataclass


@dataclass
class InstrumentReference:
    """References an Instrument with its alias to be retrieved from the Instrument Factory.

    Args:
        alias (str): The alias name of the Instrument.
        slot_id (int): The number that identifies the slot used by the instrument within the
                            the possible list of available modules (i.e. on a Cluster).
    """

    alias: str
    slot_id: int  # slot_id represents the number displayed in the cluster

    def __iter__(self):
        """Iterate over InstrumentReference elements.

        Yields:
            tuple[tuple[str], tuple[str, int], tuple[str, int]]: alias and slot_id
        """
        yield from self.__dict__.items()

    def to_dict(self):
        """Return a dict representation of the InstrumentReference class."""
        return {"alias": self.alias, "slot_id": self.slot_id}

    @classmethod
    def from_dict(cls, settings: dict):
        """Build an InstrumentReference from a settings dictionary

        Args:
            settings (dict): an instrument reference from the settings file
        """
        return InstrumentReference(**settings)
