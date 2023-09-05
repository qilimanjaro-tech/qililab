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
from typing import TypeVar

from qililab.instruments.instrument import Instrument
from qililab.typings.enums import InstrumentName

Element = TypeVar("Element", bound=Instrument)


class InstrumentFactory:
    """Hash table that loads a specific class given an object's name."""

    handlers: dict[str, type[Instrument]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[Instrument]:
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str | InstrumentName) -> type[Instrument]:
        """Return class attribute."""
        return cls.handlers[name.value] if isinstance(name, InstrumentName) else cls.handlers[name]
