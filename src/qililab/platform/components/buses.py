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

"""Buses class."""
from dataclasses import dataclass

from qililab.platform.components.bus import Bus
from qililab.system_control import ReadoutSystemControl


@dataclass
class Buses:
    """Class used as a container of :class:`Bus` objects, these are inside the `elements` attribute, as a list.

    You can add more :class:`Bus` objects to the list, you can get the :class:`Bus` object connected to a concrete port
    through the `add()` or `get()` methods respectively.

    And you can also get all the :class:`Bus` objects containing system controls used for readout via the `readout_buses` property.

    Args:
        buses (list[Bus]): List of :class:`Bus` objects.
    """

    elements: list[Bus]

    def add(self, bus: Bus):
        """Add a bus to the list of buses.

        Args:
            bus (Bus): Bus object to append."""
        self.elements.append(bus)

    def get(self, port: str):
        """Get bus connected to the specified port.

        Args:
            port (int): Port of the Chip where the bus is connected to.
        """
        bus = [bus for bus in self.elements if bus.port == port]
        if len(bus) == 1:
            return bus[0]

        raise ValueError(
            f"There can only be one bus connected to a port. There are {len(bus)} buses connected to port {port}."
        )

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over buses."""
        return self.elements.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.elements.__getitem__(key)

    def __len__(self):
        """Redirect __len__ magic method."""
        return len(self.elements)

    def to_dict(self) -> list[dict]:
        """Return a dict representation of the Buses class."""
        return [bus.to_dict() for bus in self.elements]

    def __str__(self) -> str:
        """String representation of the buses

        Returns:
            str: Buses structure representation
        """
        return "\n".join(str(bus) for bus in self.elements)

    @property
    def readout_buses(self) -> list[Bus]:
        """Returns a list of buses containing system controls used for readout."""
        return [bus for bus in self.elements if isinstance(bus.system_control, ReadoutSystemControl)]
