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

"""InstrumentInterfaceFactory class module."""
from abc import (  # The ABC is actually a BaseInstrument class, less general, and concretely only interfaces, but we don't want to cause circular imports.
    ABC,
)
from typing import TypeVar

Element = TypeVar("Element", bound=ABC)  # The ABC is actually a BaseInstrument class.


class InstrumentInterfaceFactory:
    """Hash table that loads a specific instrument interface (child of BaseInstrument) given an object's __name__.

    (Actually this factory could initialize any class that inherits from ABC which gets registered into it with @InstrumentInterfaceFactory.register)
    """

    handlers: dict[str, type[ABC]] = {}  # The ABC is actually a BaseInstrument class.

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[ABC]:  # The ABC is actually a BaseInstrument class.
        """Register handler in the factory given the class (through its __name__).

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.__name__] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> type[ABC]:  # The ABC is actually a BaseInstrument class.
        """Return class attribute given its __name__"""
        return cls.handlers[name]
