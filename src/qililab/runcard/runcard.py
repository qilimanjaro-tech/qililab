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


from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic_yaml import parse_yaml_file_as, to_yaml_file
from ruamel.yaml import YAML

from qililab.runcard.runcard_buses import RuncardBus
from qililab.runcard.runcard_instrument_controllers import RuncardInstrumentController
from qililab.runcard.runcard_instruments import RuncardInstrument

if TYPE_CHECKING:
    from qililab.buses.bus import Bus
    from qililab.instrument_controllers.instrument_controller2 import InstrumentController2
    from qililab.instruments.instrument2 import Instrument2

yaml = YAML()
yaml.width = 120


class Runcard(BaseModel):
    name: str
    buses: list[RuncardBus] = Field(default=[])
    instruments: list[RuncardInstrument] = Field(default=[])
    instrument_controllers: list[RuncardInstrumentController] = Field(default=[])

    @model_validator(mode="after")
    def validate_instrument_aliases_are_not_duplicate(self):
        alias_set = set()
        for instrument in self.instruments:
            alias = instrument.settings.alias
            if alias in alias_set:
                raise ValueError(f"Duplicate alias '{alias}' found in instruments.")
            alias_set.add(alias)
        return self

    @model_validator(mode="after")
    def validate_instrument_controller_aliases_are_not_duplicate(self):
        alias_set = set()
        for instrument_controller in self.instrument_controllers:
            alias = instrument_controller.settings.alias
            if alias in alias_set:
                raise ValueError(f"Duplicate alias '{alias}' found in instrument controllers.")
            alias_set.add(alias)
        return self

    @model_validator(mode="after")
    def validate_instrument_aliases_in_instrument_controllers_exist(self):
        runcard_instrument_aliases = {instrument.settings.alias for instrument in self.instruments}
        for instrument_controller in self.instrument_controllers:
            controller_instrument_aliases = {
                instrument_module.alias for instrument_module in instrument_controller.settings.modules
            }
            if difference := controller_instrument_aliases - runcard_instrument_aliases:
                raise ValueError(
                    f"Instrument '{next(iter(difference))}' of controller '{instrument_controller.settings.alias}' not found in runcard instruments."
                )
        return self

    @model_validator(mode="after")
    def validate_instrument_aliases_in_buses_exist(self):
        runcard_instrument_aliases = {instrument.settings.alias for instrument in self.instruments}
        for bus in self.buses:
            bus_instrument_alias = set(bus.instruments)
            if difference := bus_instrument_alias - runcard_instrument_aliases:
                raise ValueError(
                    f"Instrument '{next(iter(difference))}' of bus '{bus.alias}' not found in runcard instruments."
                )
        return self

    def add_instrument(self, instrument: "Instrument2"):
        try:
            self.instruments.append(instrument.to_runcard())
            Runcard.model_validate(self)
        except ValidationError as e:
            self.remove_instrument(instrument.settings.alias)
            raise e

    def remove_instrument(self, alias: str):
        for i, instrument in enumerate(self.instruments):
            if instrument.settings.alias == alias:
                self.instruments.pop(i)
                break

    def add_instrument_controller(self, instrument_controller: "InstrumentController2"):
        try:
            self.instrument_controllers.append(instrument_controller.to_runcard())
            Runcard.model_validate(self)
        except ValidationError as e:
            self.remove_instrument_controller(instrument_controller.settings.alias)
            raise e

    def remove_instrument_controller(self, alias: str):
        for i, instrument_controller in enumerate(self.instrument_controllers):
            if instrument_controller.settings.alias == alias:
                self.instrument_controllers.pop(i)
                break

    def add_bus(self, bus: "Bus"):
        try:
            self.buses.append(bus.to_runcard())
            Runcard.model_validate(self)
        except ValidationError as e:
            self.remove_bus(bus.alias)
            raise e

    def remove_bus(self, alias: str):
        for i, bus in enumerate(self.buses):
            if bus.alias == alias:
                self.buses.pop(i)
                break

    def save_to(self, file: str):
        to_yaml_file(file=file, model=self, custom_yaml_writer=yaml)

    @classmethod
    def load_from(cls, file: str) -> "Runcard":
        return parse_yaml_file_as(Runcard, file)
