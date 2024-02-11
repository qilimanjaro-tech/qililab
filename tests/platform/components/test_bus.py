"""Tests for the Bus class."""
import re
from types import NoneType
from unittest.mock import MagicMock, patch

import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

import qililab as ql
from qililab.exceptions import ParameterNotFound
from qililab.instruments.instrument import Instrument
from qililab.platform import Bus, Buses
from qililab.typings import Line
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

    def test_init(self, bus: Bus):
        """Test system_control instance."""
        for instrument in bus.settings.instruments:
            assert isinstance(instrument, Instrument)

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ magic method."""
        for element in bus:
            assert not isinstance(element, (NoneType, str))

    def test_print_bus(self, bus: Bus):
        """Test print bus."""
        instruments = "--".join(f"|{instrument}|" for instrument in bus.instruments)
        assert str(bus) == f"Bus {bus.alias}:  ----{instruments}----"


class TestAcquireResults:
    """Unit tests for acquiring results"""

    def test_acquire_qprogram_results(self):
        """Test acquire_qprogram_results method."""
        buses = load_buses()
        _ = [bus for bus in buses if bus.line == Line.READOUT][0]

        # with patch.object(ReadoutSystemControl, "acquire_qprogram_results") as acquire_qprogram_results:
        #     readout_bus.acquire_qprogram_results(acquisitions=["acquisition_0", "acquisition_1"])

        # acquire_qprogram_results.assert_called_once_with(acquisitions=["acquisition_0", "acquisition_1"])


class TestErrors:
    """Unit tests for the errors raised by the Bus class."""

    def test_control_bus_raises_error_when_acquiring_results(self):
        """Test that an error is raised when calling acquire_result with a drive bus."""
        buses = load_buses()
        control_bus = [bus for bus in buses if not bus.line == Line.READOUT][0]
        with pytest.raises(
            AttributeError,
            match=f"The bus {control_bus.alias} cannot acquire results because it doesn't have a readout system control",
        ):
            control_bus.acquire_result()

    def test_control_bus_raises_error_when_parameter_not_found(self):
        """Test that an error is raised when trying to set a parameter not found in bus parameters."""
        buses = load_buses()
        control_bus = [bus for bus in buses if not bus.line == Line.READOUT][0]
        parameter = ql.Parameter.GATE_OPTIONS
        error_string = re.escape(
            f"No parameter with name {parameter.value} was found in the bus with alias {control_bus.alias}"
        )
        with pytest.raises(ParameterNotFound, match=error_string):
            control_bus.get_parameter(parameter=parameter)

    def test_control_bus_raises_error_when_acquiring_qprogram_results(self):
        """Test that an error is raised when calling acquire_result with a drive bus."""
        buses = load_buses()
        control_bus = [bus for bus in buses if not bus.line == Line.READOUT][0]
        with pytest.raises(
            AttributeError,
            match=f"The bus {control_bus.alias} cannot acquire results because it doesn't have a readout system control",
        ):
            control_bus.acquire_qprogram_results(acquisitions=["acquisition_0", "acquisition_1"])
