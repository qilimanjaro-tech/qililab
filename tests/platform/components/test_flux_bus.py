"""Unittests for the FluxBus class"""
from unittest.mock import MagicMock, patch

import pytest
from qcodes import Instrument
from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyChannel

from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.spi_rack import D5aDacChannel, S4gDacChannel
from qililab.drivers.interfaces import CurrentSource, VoltageSource
from qililab.platform.components import FluxBus
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name
NUM_SLOTS = 20
START_TIME_DEFAULT = 0
START_TIME_NON_ZERO = 4
PORT = 0
ALIAS = "flux_bus_0"


def get_pulse_bus_schedule(start_time: int, negative_amplitude: bool = False, number_pulses: int = 1):
    """Returns a gaussian pulse bus schedule"""

    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=(-1 * PULSE_AMPLITUDE) if negative_amplitude else PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )
    pulse_event = PulseEvent(pulse=pulse, start_time=start_time)
    timeline = [pulse_event for _ in range(number_pulses)]

    return PulseBusSchedule(timeline=timeline, port=0)


class MockQcodesS4gD5aDacChannels(DummyChannel):
    """Mock class for Qcodes S4gDacChannel and D5aDacChannel"""

    def __init__(self, parent, name, dac, **kwargs):  # pylint: disable=unused-argument
        """Mock init method"""
        super().__init__(parent=parent, name=name, channel="", **kwargs)
        self.add_parameter(
            name="current",
            label="Current",
            unit="mA",
            get_cmd=None,
            set_cmd=None,
            get_parser=float,
            vals=vals.Numbers(0, 20e9),
        )

        self.add_parameter(
            name="voltage",
            label="Voltage",
            unit="V",
            get_cmd=None,
            set_cmd=None,
            get_parser=float,
            vals=vals.Numbers(0, 20e9),
        )
        # fake parameter for testing purposes
        self.add_parameter(
            name="status",
            label="status",
            unit="S",
            get_cmd=None,
            set_cmd=None,
            get_parser=float,
            vals=vals.Numbers(0, 20e9),
        )

    def _get_current(self, dac: int) -> float:  # pylint: disable=unused-argument
        """
        Gets the current set by the module.

        Args:
            dac (int): the dac of which to get the current

        Returns:
            self.current (float): The output current reported by the hardware
        """
        return self.current

    def _get_voltage(self, dac: int) -> float:  # pylint: disable=unused-argument
        """
        Gets the voltage set by the module.

        Args:
            dac (int): the dac of which to get the current

        Returns:
            self.voltage (float): The output voltage reported by the hardware
        """
        return self.voltage


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return get_pulse_bus_schedule(start_time=0)


@pytest.fixture(name="sequencer")
def fixture_sequencer() -> SequencerQCM:
    """Return SequencerQCM instance."""
    sequencer = SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)
    sequencer.add_parameter(
        name="status",
        label="status",
        unit="S",
        get_cmd=None,
        set_cmd=None,
        get_parser=float,
        vals=vals.Numbers(0, 20e9),
    )
    return sequencer


@pytest.fixture(name="voltage_source")
def fixture_voltage_source() -> D5aDacChannel:
    """Return D5aDacChannel instance."""
    return D5aDacChannel(parent=MagicMock(), name="test_d5a_dac_channel", dac=0)


@pytest.fixture(name="current_source")
def fixture_current_source() -> S4gDacChannel:
    """Return S4gDacChannel instance."""
    return S4gDacChannel(parent=MagicMock(), name="test_s4g_dac_channel", dac=0)


@pytest.fixture(name="flux_bus_current_source")
def fixture_flux_bus_current_source(sequencer: SequencerQCM, current_source: S4gDacChannel) -> FluxBus:
    """Return FluxBus instance with current source."""
    return FluxBus(alias=ALIAS, port=PORT, awg=sequencer, source=current_source)


@pytest.fixture(name="flux_bus_voltage_source")
def fixture_flux_bus_voltage_source(sequencer: SequencerQCM, voltage_source: D5aDacChannel) -> FluxBus:
    """Return FluxBus instance with voltage source."""
    return FluxBus(alias=ALIAS, port=PORT, awg=sequencer, source=voltage_source)


class TestFluxBus:
    """Unit tests checking the FluxBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""
        cls.old_sg4_bases = S4gDacChannel.__bases__
        cls.old_d5a_bases = D5aDacChannel.__bases__
        S4gDacChannel.__bases__ = (MockQcodesS4gD5aDacChannels, CurrentSource)
        D5aDacChannel.__bases__ = (MockQcodesS4gD5aDacChannels, VoltageSource)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""
        S4gDacChannel.__bases__ = cls.old_sg4_bases
        D5aDacChannel.__bases__ = cls.old_d5a_bases

    def teardown_method(self):
        """Close all instruments after each test has been run"""
        Instrument.close_all()

    def test_init_voltage_source(self, flux_bus_voltage_source: FluxBus):
        """Test init method with voltage source"""
        assert isinstance(flux_bus_voltage_source.instruments["awg"], SequencerQCM)
        assert isinstance(flux_bus_voltage_source.instruments["source"], D5aDacChannel)

    def test_init_current_source(self, flux_bus_current_source: FluxBus):
        """Test init method with current source"""
        assert isinstance(flux_bus_current_source.instruments["awg"], SequencerQCM)
        assert isinstance(flux_bus_current_source.instruments["source"], S4gDacChannel)

    def test_set_with_voltage_source(self, flux_bus_voltage_source: FluxBus):
        """Test set method with voltage source"""
        # Testing with parameters that exists
        sequencer_param = "channel_map_path0_out0_en"
        voltage_source_param = "voltage"
        voltage_source_param_value = 0.03
        flux_bus_voltage_source.set(param_name=sequencer_param, value=True)
        flux_bus_voltage_source.set(param_name=voltage_source_param, value=voltage_source_param_value)

        assert flux_bus_voltage_source.instruments["awg"].get(sequencer_param) is True
        assert flux_bus_voltage_source.instruments["source"].get(voltage_source_param) == voltage_source_param_value

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            flux_bus_voltage_source.set(param_name=random_param, value=True)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            flux_bus_voltage_source.set(param_name=duplicated_param, value=True)

    def test_set_with_current_source(self, flux_bus_current_source: FluxBus):
        """Test set method with current source"""
        # Testing with parameters that exist
        sequencer_param = "channel_map_path0_out0_en"
        current_source_param = "current"
        current_source_param_value = 0.03
        flux_bus_current_source.set(param_name=sequencer_param, value=True)
        flux_bus_current_source.set(param_name=current_source_param, value=current_source_param_value)

        assert flux_bus_current_source.instruments["awg"].get(sequencer_param) is True
        assert flux_bus_current_source.instruments["source"].get(current_source_param) == current_source_param_value

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            flux_bus_current_source.set(param_name=random_param, value=True)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            flux_bus_current_source.set(param_name=duplicated_param, value=True)

    def test_get_with_voltage_source(self, flux_bus_voltage_source: FluxBus):
        """Test get method with voltage source"""
        # testing with parameters that exist
        sequencer_param = "channel_map_path0_out0_en"
        voltage_source_param = "voltage"
        voltage_source_param_value = 0.03
        flux_bus_voltage_source.set(param_name=sequencer_param, value=True)
        flux_bus_voltage_source.set(param_name=voltage_source_param, value=voltage_source_param_value)

        assert flux_bus_voltage_source.get(sequencer_param) is True
        assert flux_bus_voltage_source.get(voltage_source_param) == voltage_source_param_value

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            flux_bus_voltage_source.set(param_name=random_param, value=True)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            flux_bus_voltage_source.set(param_name=duplicated_param, value=True)

    def test_get_with_current_source(self, flux_bus_current_source: FluxBus):
        """Test get method with voltage source"""
        # testing with parameters that exist
        sequencer_param = "channel_map_path0_out0_en"
        current_source_param = "current"
        current_source_param_value = 0.03
        flux_bus_current_source.set(param_name=sequencer_param, value=True)
        flux_bus_current_source.set(param_name=current_source_param, value=current_source_param_value)

        assert flux_bus_current_source.get(sequencer_param) is True
        assert flux_bus_current_source.get(current_source_param) == current_source_param_value

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            flux_bus_current_source.set(param_name=random_param, value=True)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            flux_bus_current_source.set(param_name=duplicated_param, value=True)

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute(
        self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, flux_bus_current_source: FluxBus
    ):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        flux_bus_current_source.execute(
            pulse_bus_schedule=pulse_bus_schedule,
            nshots=nshots,
            repetition_duration=repetition_duration,
            num_bins=num_bins,
        )

        mock_execute.assert_called_once_with(
            pulse_bus_schedule=pulse_bus_schedule,
            nshots=nshots,
            repetition_duration=repetition_duration,
            num_bins=num_bins,
        )

    def test_str(self, flux_bus_current_source: FluxBus):
        """Unittest for __str__ method."""
        expected_str = (
            f"{ALIAS} ({flux_bus_current_source.__class__.__name__}): "
            + "".join(f"--|{instrument.name}|" for instrument in flux_bus_current_source.instruments.values())
            + f"--> port {flux_bus_current_source.port}"
        )

        assert str(flux_bus_current_source) == expected_str