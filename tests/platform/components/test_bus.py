"""Tests for the Bus class."""
from __future__ import annotations

import re
from types import NoneType
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call, create_autospec

import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.data_management import build_platform
from qililab.exceptions import ParameterNotFound
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.platform.components.bus import Bus
from qililab.typings.enums import Parameter
from tests.data import SauronQDevil

# if TYPE_CHECKING:
#     from qililab.platform import Platform


@pytest.fixture(name="bus_and_mocks")
def bus_and_mocks():
    """Return bus object and necessary mocks"""

    # Create a mock Instruments container
    mock_instruments_container = MagicMock(spec=Instruments)
    # Mock Instrument class for testing
    mock_instrument = create_autospec(Instrument)

    # Setup the mock to return a mock instrument when get_instrument is called
    mock_instruments_container.get_instrument.return_value = mock_instrument

    # Example settings for your Bus initialization
    settings = {
        "alias": "bus1",
        "instruments": ["instrument1", "instrument2"],
        "channels": [1, 2],
    }

    # Instantiate Bus with mocked instruments
    bus = Bus(settings=settings, platform_instruments=mock_instruments_container)

    # Return both the bus instance and the mocks for further assertions in tests
    return bus, mock_instruments_container, settings["instruments"]


@pytest.fixture(name="platform")
def fixture_platform():
    """Return platform"""
    return build_platform(runcard=SauronQDevil.runcard)


@pytest.fixture(name="qpysequence")
def fixture_qpysequence() -> Sequence:
    """Return Sequence instance."""
    return Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())


class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_init(self, bus_and_mocks):
        """Test system_control instance."""
        bus, mock_instruments_container, aliases = bus_and_mocks

        # Assertions for instruments instantiation
        assert len(bus.settings.instruments) == len(aliases), "Number of instruments does not match expected"
        for inst in bus.settings.instruments:
            assert isinstance(inst, Instrument), "Instrument is not an instance of the Instrument class"

        # Verify get_instrument was called with the correct aliases
        mock_instruments_container.get_instrument.assert_has_calls(
            [call(alias=alias) for alias in aliases], any_order=True
        )


#     def test_iter_and_getitem_methods(self, platform):
#         """Test __iter__ magic method."""
#         for bus in platform.buses:
#             for element in bus:
#                 assert not isinstance(element, (NoneType, str))

#     def test_print_bus(self, platform):
#         """Test print bus."""
#         for bus in platform.buses:
#             instruments = "--".join(f"|{instrument}|" for instrument in bus.instruments)
#             assert str(bus) == f"Bus {bus.alias}:  ----{instruments}----"


# class TestAcquireResults:
#     """Unit tests for acquiring results"""

#     def test_acquire_qprogram_results(self):
#         """Test acquire_qprogram_results method."""
#         # buses = load_buses()
#         # _ = [bus for bus in buses if bus.line == Line.READOUT][0]

#         # with patch.object(ReadoutSystemControl, "acquire_qprogram_results") as acquire_qprogram_results:
#         #     readout_bus.acquire_qprogram_results(acquisitions=["acquisition_0", "acquisition_1"])

#         # acquire_qprogram_results.assert_called_once_with(acquisitions=["acquisition_0", "acquisition_1"])


# class TestErrors:
#     """Unit tests for the errors raised by the Bus class."""

#     def test_control_bus_raises_error_when_acquiring_results(self, platform):
#         """Test that an error is raised when calling acquire_result with a drive bus."""
#         control_bus = [bus for bus in platform.buses if not bus.has_adc()][0]
#         with pytest.raises(
#             AttributeError,
#             match=f"The bus {control_bus.alias} cannot acquire results because it doesn't have a readout system control",
#         ):
#             control_bus.acquire_result()

#     def test_control_bus_raises_error_when_parameter_not_found(self, platform):
#         """Test that an error is raised when trying to set a parameter not found in bus parameters."""
#         control_bus = [bus for bus in platform.buses if not bus.has_adc()][0]
#         parameter = Parameter.GATE_OPTIONS
#         error_string = re.escape(
#             f"No parameter with name {parameter.value} was found in the bus with alias {control_bus.alias}"
#         )
#         with pytest.raises(ParameterNotFound, match=error_string):
#             control_bus.get_parameter(parameter=parameter)

#     def test_control_bus_raises_error_when_acquiring_qprogram_results(self, platform):
#         """Test that an error is raised when calling acquire_result with a drive bus."""
#         control_bus = [bus for bus in platform.buses if not bus.has_adc()][0]
#         with pytest.raises(
#             AttributeError,
#             match=f"The bus {control_bus.alias} cannot acquire results because it doesn't have a readout system control",
#         ):
#             control_bus.acquire_qprogram_results(acquisitions=["acquisition_0", "acquisition_1"])
