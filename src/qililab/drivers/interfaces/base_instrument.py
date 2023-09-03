"""SignalGenerator class."""
from abc import ABC, abstractmethod
from typing import Any

from qcodes.instrument import InstrumentBase
from qcodes.parameters import ParameterBase


class BaseInstrument(ABC):
    """Base Interface for all instruments.

    Args:
        params_set (dict): The parameters that have been set to a specific value.
    """

    params_set: dict = {}

    @property
    @abstractmethod
    def params(self):
        """parameters property."""

    @property
    @abstractmethod
    def alias(self):
        """alias property."""

    def add_parameter(
        self,
        name: str,
        parameter_class: type[ParameterBase] | None = None,
        **kwargs: Any,
    ) -> None:
        """Corrects QCodes add_parameter so it saves the parameters set into params_set.'

        Args:
            name: How the parameter will be stored within
                :attr:`.parameters` and also how you address it using the
                shortcut methods: ``instrument.set(param_name, value)`` etc.

            parameter_class: You can construct the parameter
                out of any class. Default :class:`.parameters.Parameter`.

            **kwargs: Constructor arguments for ``parameter_class``.
        """
        if "initial_value" in kwargs:
            self.params_set[name] = kwargs["initial_value"]

        InstrumentBase.add_parameter(self, name, parameter_class, **kwargs)  # type: ignore

    def set(self, param_name: str, value: Any):
        """Sets a parameter value and saves it into params_set.

        Args:
            param_name (str): Parameter name
            value (Any): Parameter value
        """
        self.params_set[param_name] = value
        InstrumentBase.set(self, param_name, value)  # type: ignore

    @abstractmethod
    def get(self, param_name: str) -> Any:
        """Get instrument parameter.

        Args:
            param_name (str): The name of a parameter of this instrument.

        Returns:
            Any: Current value of the parameter.
        """
