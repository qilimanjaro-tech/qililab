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

from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic_yaml import parse_yaml_file_as, to_yaml_file
from ruamel.yaml import YAML

from qililab.instruments.instrument2 import Instrument2
from qililab.instruments.instrument_type import InstrumentType
from qililab.settings.instruments import QDevilQDAC2Settings

yaml = YAML()
yaml.width = 120


class RuncardQDevilQDAC2Instrument(BaseModel):
    type: Literal[InstrumentType.QDEVIL_QDAC2] = InstrumentType.QDEVIL_QDAC2
    settings: QDevilQDAC2Settings


# Discriminated Union for instruments
RuncardInstrument = Annotated[RuncardQDevilQDAC2Instrument, Field(discriminator="type")]


class Runcard(BaseModel):
    name: str
    instruments: list[RuncardInstrument] = Field(default=[])

    @model_validator(mode="after")
    def validate_aliases(self):
        alias_set = set()
        for instrument in self.instruments:
            alias = instrument.settings.alias
            if alias in alias_set:
                raise ValueError(f"Duplicate alias '{alias}' found in instruments.")
            alias_set.add(alias)
        return self

    def add_instrument(self, instrument: Instrument2):
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

    def save_to(self, file: str):
        to_yaml_file(file=file, model=self, custom_yaml_writer=yaml)

    @classmethod
    def load_from(cls, file: str) -> "Runcard":
        return parse_yaml_file_as(Runcard, file)
