"""Tests for the Bus class."""
from types import NoneType
from unittest.mock import MagicMock

import pytest

from qililab.instruments.instrument import ParameterNotFound
from qililab.platform import Bus
from qililab.system_control import SystemControl
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
        print(bus)

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
