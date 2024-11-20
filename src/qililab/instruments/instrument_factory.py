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

from typing import TYPE_CHECKING, ClassVar, Dict, Type

from qililab.instruments.instrument_type import InstrumentType

if TYPE_CHECKING:
    from qililab.instruments.instrument2 import Instrument2
    from qililab.runcard.runcard import RuncardInstrument


# InstrumentFactory singleton class with class methods
class InstrumentFactory:
    _registry: ClassVar[Dict[InstrumentType, Type["Instrument2"]]] = {}

    @classmethod
    def register_instrument(cls, instrument_type: InstrumentType):
        def decorator(instrument_cls):
            cls._registry[instrument_type] = instrument_cls
            return instrument_cls

        return decorator

    @classmethod
    def create_instrument(cls, runcard_instrument: "RuncardInstrument") -> "Instrument2":
        instrument_type = runcard_instrument.type
        instrument_class = cls._registry.get(instrument_type)
        if instrument_class is None:
            raise ValueError(f"Unknown instrument type: {instrument_type}")
        return instrument_class(settings=runcard_instrument.settings)
