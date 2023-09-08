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

"""InstrumentFactory class."""
from enum import Enum
from typing import TypeVar

from qililab.instrument_controllers.instrument_controller import InstrumentController

Element = TypeVar("Element", bound=InstrumentController)


class InstrumentControllerFactory:
    """Hash table that loads a specific class given an object's name."""

    handlers: dict[str, type[InstrumentController]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[InstrumentController]:
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str | Enum) -> type[InstrumentController]:
        """Return class attribute."""
        return cls.handlers[name.value] if isinstance(name, Enum) else cls.handlers[name]
