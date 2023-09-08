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

"""SignalGenerator class."""
from abc import ABC, abstractmethod
from typing import Any


class BaseInstrument(ABC):
    """Base Interface for all instruments."""

    @property
    @abstractmethod
    def params(self):
        """parameters property."""

    @property
    @abstractmethod
    def alias(self):
        """alias property."""

    @abstractmethod
    def set(self, param_name: str, value: Any) -> None:
        """Set instrument parameter.

        Args:
            param_name (str): The name of a parameter of this instrument.
            value (Any): The new value to set.
        """

    @abstractmethod
    def get(self, param_name: str) -> Any:
        """Get instrument parameter.

        Args:
            param_name (str): The name of a parameter of this instrument.

        Returns:
            Any: Current value of the parameter.
        """

    def instrument_repr(self) -> dict[str, Any]:
        """Returns a dictionary representation of the instrument, parameters and submodules.
        Returns:
            inst_repr (dict[str, Any]): Instrument representation
        """
        inst_repr: dict[str, Any] = {
            "alias": self.alias,
        }

        params: dict[str, Any] = {}
        for param_name in self.params:
            param_value = self.get(param_name)
            params[param_name] = param_value
        inst_repr["parameters"] = params

        return inst_repr

    def initial_setup(self, params: dict[str, Any] | None = None):
        """Initializes the parameters of the instrument and of the submodules.

        Args:
            setup_dict (dict[str, Any]): Dictionary representation.
        """
        if params:
            for param_name, value in params.items():
                self.set(param_name=param_name, value=value)