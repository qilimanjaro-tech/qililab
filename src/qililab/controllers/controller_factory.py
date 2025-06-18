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
    from qililab.controllers.controller import Controller
    from qililab.controllers.controller_type import ControllerType
    from qililab.runcard.runcard_controllers import RuncardController


# Factory for creating Controllers
class ControllerFactory:
    _registry: ClassVar[dict[ControllerType, Type[Controller]]] = {}

    @classmethod
    def register(cls, type: ControllerType):
        def decorator(instrument_cls):
            cls._registry[type] = instrument_cls
            return instrument_cls

        return decorator

    @classmethod
    def create(cls, runcard_instrument_controller: RuncardController) -> "Controller":
        instrument_controller_type = runcard_instrument_controller.type
        instrument_class = cls._registry.get(instrument_controller_type)
        if instrument_class is None:
            raise ValueError(f"Unknown instrument type: {instrument_controller_type}")
        return instrument_class(settings=runcard_instrument_controller.settings)
