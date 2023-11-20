"""Tests for the Bus class."""
from types import NoneType
from unittest.mock import MagicMock, patch

import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.instruments.instrument import ParameterNotFound
from qililab.platform import Bus, Buses
from qililab.system_control import ReadoutSystemControl, SystemControl
from qililab.typings import Parameter
from tests.data import Galadriel
from tests.test_utils import build_platform


def load_buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    platform = build_platform(Galadriel.runcard)
    return platform.buses


@pytest.fixture(name="qpysequence")
def fixture_qpysequence() -> Sequence:
    """Return Sequence instance."""
    return Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())


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
        bus.system_control.set_parameter.assert_called_once_with(
            parameter=Parameter.GAIN, value=0.5, channel_id=None, port_id=bus.port
        )

    def test_set_parameter_raises_error(self, bus: Bus):
        """Test set_parameter method raises error."""
        bus.settings.system_control = MagicMock()
        bus.settings.system_control.set_parameter.side_effect = ParameterNotFound(message="dummy error")
        with pytest.raises(
            ParameterNotFound, match=f"No parameter with name duration was found in the bus with alias {bus.alias}"
        ):
            bus.set_parameter(parameter=Parameter.DURATION, value=0.5, channel_id=1)

    def test_upload_qpysequence(self, bus: Bus, qpysequence: Sequence):
        """Test upload_qpysequence method."""
        bus.settings.system_control = MagicMock()
        bus.upload_qpysequence(qpysequence=qpysequence)
        bus.system_control.upload_qpysequence.assert_called_once_with(qpysequence=qpysequence, port=bus.port)


class TestAcquireResults:
    """Unit tests for acquiring results"""

    def test_acquire_qprogram_results(self):
        """Test acquire_qprogram_results method."""
        buses = load_buses()
        readout_bus = [bus for bus in buses if isinstance(bus.system_control, ReadoutSystemControl)][0]

        with patch.object(ReadoutSystemControl, "acquire_qprogram_results") as acquire_qprogram_results:
            readout_bus.acquire_qprogram_results(acquisitions=["acquisition_0", "acquisition_1"])

        acquire_qprogram_results.assert_called_once_with(acquisitions=["acquisition_0", "acquisition_1"])


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

    def test_control_bus_raises_error_when_acquiring_qprogram_results(self):
        """Test that an error is raised when calling acquire_result with a drive bus."""
        buses = load_buses()
        control_bus = [bus for bus in buses if not isinstance(bus.system_control, ReadoutSystemControl)][0]
        with pytest.raises(
            AttributeError,
            match=f"The bus {control_bus.alias} cannot acquire results because it doesn't have a readout system control",
        ):
            control_bus.acquire_qprogram_results(acquisitions=["acquisition_0", "acquisition_1"])
