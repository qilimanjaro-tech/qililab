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

    @abstractmethod
    def instrument_repr(self) -> dict[str, Any]:
        """Returns a dictionary representation of the instrument, parameters and submodules.

        Returns:
            dict[str, Any]: Instrument representation
        """

    def initial_setup(self, params: dict[str, Any] | None = None):
        """Initializes the parameters of the instrument and of the submodules.

        Args:
            setup_dict (dict[str, Any]): Dictionary representation.
        """
        if params:
            for param_name, value in params.items():
                self.set(param_name=param_name, value=value)
