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

"""Runcard class."""

from dataclasses import dataclass, field

from qililab.settings.analog.analog_compilation_settings import AnalogCompilationSettings
from qililab.settings.bus_settings import BusSettings
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings


@dataclass
class Runcard:
    """Runcard class. Casts the platform dictionary into a class.

    The input to the constructor should be a dictionary of the desired runcard with the following structure:
    - gates_settings:
    - buses:
    - instruments: List of "instruments" dictionaries
    - instrument_controllers: List of "instrument_controllers" dictionaries

    The gates_settings and bus dictionaries will be passed to their corresponding Runcard.GatesSettings and Runcard.Bus
    classes here, meanwhile the instruments and instrument_controllers will remain dictionaries.

    Then this full class gets passed to the Platform who will instantiate the actual Buses/Bus and the
    corresponding Instrument classes with the settings attributes of this class.

    Args:
        gates_settings (dict): Gates settings dictionary -> Runcard.GatesSettings inner dataclass
        buses (list[dict]): List of Bus settings dictionaries -> list[Runcard.Bus] settings inner dataclass
        instruments (list[dict]): List of dictionaries containing the "instruments" information (does not transform)
        instruments_controllers (list[dict]): List of dictionaries containing the "instrument_controllers" information
            (does not transform)
    """

    name: str
    instruments: list[dict] = field(default_factory=list)
    instrument_controllers: list[dict] = field(default_factory=list)
    buses: list[BusSettings] = field(default_factory=list)
    digital: DigitalCompilationSettings | None = None
    analog: AnalogCompilationSettings | None = None

    def __post_init__(self):
        self.buses = [BusSettings(**bus) for bus in self.buses]
        self.digital = DigitalCompilationSettings(**self.digital) if self.digital is not None else None
        self.analog = AnalogCompilationSettings(**self.analog) if self.analog is not None else None
