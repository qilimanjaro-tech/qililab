"""Tests for the Bus class."""
from types import NoneType
from unittest.mock import MagicMock

import pytest

from qililab.instruments.instrument import ParameterNotFound
from qililab.platform import Bus
from qililab.system_control import ReadoutSystemControl, SystemControl
from qililab.typings import Parameter

from .aux_methods import buses as load_buses


@pytest.mark.parametrize("bus", [load_buses().elements[0], load_buses().elements[1]])
class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_system_control_instance(self, bus: Bus):
        """Test system_control instance."""
        assert isinstance(bus.system_control, SystemControl)

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ magic method."""
        for element in bus:
            assert not isinstance(element, (NoneType, str))

    def test_print_bus(self, bus: Bus):
        """Test print bus."""
        assert str(bus) == f"Bus {bus.alias}:  ----{bus.system_control}---" + "".join(
            f"--|{target}|----" for target in bus.targets
        )

    def test_set_parameter(self, bus: Bus):
        """Test set_parameter method."""
        bus.settings.system_control = MagicMock()
        bus.set_parameter(parameter=Parameter.GAIN, value=0.5)
        bus.system_control.set_parameter.assert_called_once_with(parameter=Parameter.GAIN, value=0.5, channel_id=None)

    def test_set_parameter_raises_error(self, bus: Bus):
        """Test set_parameter method raises error."""
        bus.settings.system_control = MagicMock()
        bus.settings.system_control.set_parameter.side_effect = ParameterNotFound(message="dummy error")
        with pytest.raises(
            ParameterNotFound, match=f"No parameter with name duration was found in the bus with alias {bus.alias}"
        ):
            bus.set_parameter(parameter=Parameter.DURATION, value=0.5, channel_id=1)


class TestErrors:
    """Unit tests for the errors raised by the Bus class."""

    def test_control_bus_raises_error_when_acquiring_results(self):
        """Test that an error is raised when calling acquire_result with a drive bus."""
        buses = load_buses()
        control_bus = [bus for bus in buses if not isinstance(bus.system_control, ReadoutSystemControl)][0]
        with pytest.raises(
            AttributeError,
            match=f"The bus {control_bus.alias} cannot acquire results because it doesn't have a readout system control",
        ):
            control_bus.acquire_result()
