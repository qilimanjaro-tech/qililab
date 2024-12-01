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

from typing import TYPE_CHECKING, ClassVar, Type

if TYPE_CHECKING:
    from qililab.instrument_controllers.instrument_controller import InstrumentController
    from qililab.instrument_controllers.instrument_controller_type import InstrumentControllerType
    from qililab.instruments.instrument import Instrument
    from qililab.runcard.runcard_instrument_controllers import RuncardInstrumentController


# InstrumentFactory singleton class with class methods
class InstrumentControllerFactory:
    _registry: ClassVar[dict[InstrumentControllerType, Type[InstrumentController]]] = {}

    @classmethod
    def register(cls, type: InstrumentControllerType):
        def decorator(instrument_cls):
            cls._registry[type] = instrument_cls
            return instrument_cls

        return decorator

    @classmethod
    def create(
        cls,
        runcard_instrument_controller: RuncardInstrumentController,
        loaded_instruments: list[Instrument] | None = None,
    ) -> "InstrumentController":
        instrument_type = runcard_instrument_controller.type
        instrument_class = cls._registry.get(instrument_type)
        if instrument_class is None:
            raise ValueError(f"Unknown instrument type: {instrument_type}")
        return instrument_class(settings=runcard_instrument_controller.settings, loaded_instruments=loaded_instruments)
