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
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Dict, Type

if TYPE_CHECKING:
    from qililab.instruments.instrument import Instrument
    from qililab.instruments.instrument_type import InstrumentType
    from qililab.runcard.runcard_instruments import RuncardInstrument


# InstrumentFactory singleton class with class methods
class InstrumentFactory:
    _registry: ClassVar[Dict[InstrumentType, Type[Instrument]]] = {}

    @classmethod
    def register(cls, instrument_type: InstrumentType):
        def decorator(instrument_cls: type[Instrument]):
            cls._registry[instrument_type] = instrument_cls
            return instrument_cls

        return decorator

    @classmethod
    def get(cls, instrument_type: InstrumentType):
        instrument_class = cls._registry.get(instrument_type)
        if instrument_class is None:
            raise ValueError(f"Unknown instrument type: {instrument_type}")
        return instrument_class()

    @classmethod
    def from_runcard(cls, runcard_instrument: RuncardInstrument) -> Instrument:
        instrument_type = runcard_instrument.type
        instrument_class = cls._registry.get(instrument_type)
        if instrument_class is None:
            raise ValueError(f"Unknown instrument type: {instrument_type}")
        return instrument_class(settings=runcard_instrument.settings)
