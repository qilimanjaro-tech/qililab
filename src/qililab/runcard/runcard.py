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


from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic_yaml import parse_yaml_file_as, to_yaml_file
from ruamel.yaml import YAML

# from qililab.buses.bus import Bus
from qililab.controllers.controller import Controller
from qililab.controllers.controller_factory import ControllerFactory

# from qililab.runcard.runcard_buses import RuncardBus
from qililab.runcard.runcard_controllers import RuncardController

yaml = YAML()
yaml.width = 120


class Runcard(BaseModel):
    name: str
    # buses: list[RuncardBus] = Field(default=[])
    controllers: list[RuncardController] = Field(default=[])

    @model_validator(mode="after")
    def validate_instrument_controller_aliases_are_not_duplicate(self):
        alias_set = set()
        for instrument_controller in self.controllers:
            alias = instrument_controller.settings.alias
            if alias in alias_set:
                raise ValueError(f"Duplicate alias '{alias}' found in instrument controllers.")
            alias_set.add(alias)
        return self

    def add_controller(self, controller: Controller):
        try:
            self.controllers.append(controller.to_runcard())
            Runcard.model_validate(self)
        except ValidationError as e:
            self.remove_controller(controller.settings.alias)
            raise e

    def remove_controller(self, alias: str):
        for i, controller in enumerate(self.controllers):
            if controller.settings.alias == alias:
                self.controllers.pop(i)
                break

    def get_controllers(self):
        return [
            ControllerFactory.create(runcard_instrument_controller)
            for runcard_instrument_controller in self.controllers
        ]

    def save_to(self, file: str):
        to_yaml_file(file=file, model=self, custom_yaml_writer=yaml)

    @classmethod
    def load_from(cls, file: str) -> "Runcard":
        return parse_yaml_file_as(Runcard, file)
