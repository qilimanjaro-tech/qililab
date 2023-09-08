""" Unit testing module for the Factory of instrument drivers"""
from typing import Any
from qililab.drivers.interfaces import BaseInstrument

class TestInstrument(BaseInstrument):
    """Testing class implementing BaseInstrument methods and properties."""

    def __init__(self):
        """Initialize the instrument."""
        self.name = "test_instrument"
        self.parameters = {}

    def set(self, param_name: str, value: Any) -> None:
        """Set instrument parameter.

        Args:
            param_name (str): The name of a parameter of this instrument.
            value (Any): The new value to set.
        """
        self.parameters[param_name] = value

    def get(self, param_name: str) -> Any:
        """Get instrument parameter.

        Args:
            param_name (str): The name of a parameter of this instrument.

        Returns:
            Any: Current value of the parameter.
        """
        return self.parameters.get(param_name, None)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name

class TestBaseInstrument:
    """Unit test for BaseInstrument interface not abstract methods"""
    def __init__(self):
        self.instrument = TestInstrument()
        self.instrument.set(param_name="param_0", value=10)
        self.instrument.set(param_name="param_1", value=1)

    def test_set(self):
        """Test that the set method sets the parameter value."""
        assert self.instrument.parameters["param"] == 10

    def test_get(self):
        """Test that the get method returns a parameter value."""
        assert self.instrument.get(param_name="param") == 10

    def test_params(self):
        """Test that the params method returns the BaseInstrument parameters."""
        expected_dict = {
            "param_0": 10,
            "param_1": 1
        }

        for key, value in expected_dict.items():
            assert key in self.instrument.params
            assert self.instrument.params[key] == value

    def test_alias(self):
        """Test that the alias method returns the instrument name."""
        assert self.instrument.alias == self.instrument.name

    def test_instrument_repr(self):
        """Test that the instrument_repr method returns the right representation."""
        expected_dict = {
            "alias": "test_instrument",
            "param_0": 10,
            "param_1": 1
        }
        instrument_reptr = self.instrument.instrument_repr()

        for key, value in expected_dict.items():
            assert key in instrument_reptr
            assert instrument_reptr[key] == value

    def test_initial_setup(self):
        """Test that the initial_setup method sets all parameters."""
        default_params = {
            "param_0": 10,
            "param_1": 1
        }
        initial_params = {
            "param_2": 20,
            "param_3": 2
        }
        self.instrument.initial_setup(params=initial_params)

        for key, value in default_params.items():
            assert key in self.instrument.params
            assert self.instrument.params[key] == value

        for key, value in initial_params.items():
            assert key in self.instrument.params
            assert self.instrument.params[key] == value
