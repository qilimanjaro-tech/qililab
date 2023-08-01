"""Unittests for the FluxBus class"""
from unittest.mock import MagicMock, patch

import pytest
from qcodes import Instrument
from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyChannel

from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.spi_rack import D5aDacChannel, S4gDacChannel
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


class MockQcodesS4gD5aDacChannels(DummyChannel):
    """Mock class for Qcodes S4gDacChannel and D5aDacChannel"""

    def __init__(self, parent, name, dac, **kwargs):
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

    def _get_current(self, dac: int) -> float:
        """
        Gets the current set by the module.

        Args:
            dac (int): the dac of which to get the current

        Returns:
            self.current (float): The output current reported by the hardware
        """
        return self.current

    def _get_voltage(self, dac: int) -> float:
        """
        Gets the voltage set by the module.

        Args:
            dac (int): the dac of which to get the current

        Returns:
            self.voltage (float): The output voltage reported by the hardware
        """
        return self.voltage

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


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""

    return get_pulse_bus_schedule(start_time=0)


@pytest.fixture(name="sequencer")
def fixture_sequencer() -> SequencerQCM:
    """Return SequencerQCM instance."""
    sequencer = SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)

    return sequencer


@pytest.fixture(name="voltage_source")
def fixture_voltage_source() -> D5aDacChannel:
    """Return D5aDacChannel instance."""
    voltage_source = D5aDacChannel(parent=MagicMock(), name="test_d5a_dac_channel", dac=0)

    return voltage_source


@pytest.fixture(name="current_source")
def fixture_current_source() -> S4gDacChannel:
    """Return S4gDacChannel instance."""
    current_source = S4gDacChannel(parent=MagicMock(), name="test_s4g_dac_channel", dac=0)

    return current_source


class TestFluxBus:
    """Unit tests checking the FluxBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_sg4_bases = S4gDacChannel.__bases__
        cls.old_d5a_bases = D5aDacChannel.__bases__
        S4gDacChannel.__bases__ = (MockQcodesS4gD5aDacChannels,)
        D5aDacChannel.__bases__ = (MockQcodesS4gD5aDacChannels,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        S4gDacChannel.__bases__ = cls.old_sg4_bases
        D5aDacChannel.__bases__ = cls.old_d5a_bases

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init_voltage_source(self, sequencer: SequencerQCM, voltage_source: D5aDacChannel):
        """Test init method with voltage source"""
        flux_bus = FluxBus(awg=sequencer, source=voltage_source)

        assert isinstance(flux_bus.awg, SequencerQCM)
        assert isinstance(flux_bus.source, D5aDacChannel)

    def test_init_current_source(self, sequencer: SequencerQCM, current_source: S4gDacChannel):
        """Test init method with current source"""
        flux_bus = FluxBus(awg=sequencer, source=current_source)

        assert isinstance(flux_bus.awg, SequencerQCM)
        assert isinstance(flux_bus.source, S4gDacChannel)

    def test_set_with_voltage_source(self, sequencer: SequencerQCM, voltage_source: D5aDacChannel):
        """Test set method with voltage source"""
        sequencer_param = "channel_map_path0_out0_en"
        voltage_source_param = "voltage"
        voltage_source_param_value = 0.03
        flux_bus = FluxBus(awg=sequencer, source=voltage_source)
        flux_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        flux_bus.set(instrument_name="source", param_name=voltage_source_param, value=voltage_source_param_value)

        assert flux_bus.awg.get(sequencer_param) is True
        assert flux_bus.source.get(voltage_source_param) == voltage_source_param_value

    def test_set_with_current_source(self, sequencer: SequencerQCM, current_source: S4gDacChannel):
        """Test set method with current source"""
        sequencer_param = "channel_map_path0_out0_en"
        current_source_param = "current"
        current_source_param_value = 0.03
        flux_bus = FluxBus(awg=sequencer, source=current_source)
        flux_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        flux_bus.set(instrument_name="source", param_name=current_source_param, value=current_source_param_value)

        assert flux_bus.awg.get(sequencer_param) is True
        assert flux_bus.source.get(current_source_param) == current_source_param_value

    def test_get_with_voltage_source(self, sequencer: SequencerQCM, voltage_source: D5aDacChannel):
        """Test get method with voltage source"""
        sequencer_param = "channel_map_path0_out0_en"
        voltage_source_param = "voltage"
        voltage_source_param_value = 0.03
        flux_bus = FluxBus(awg=sequencer, source=voltage_source)
        flux_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        flux_bus.set(instrument_name="source", param_name=voltage_source_param, value=voltage_source_param_value)

        assert flux_bus.get("awg", sequencer_param) is True
        assert flux_bus.get("source", voltage_source_param) == voltage_source_param_value

    def test_get_with_current_source(self, sequencer: SequencerQCM, current_source: S4gDacChannel):
        """Test get method with voltage source"""
        sequencer_param = "channel_map_path0_out0_en"
        current_source_param = "current"
        current_source_param_value = 0.03
        flux_bus = FluxBus(awg=sequencer, source=current_source)
        flux_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        flux_bus.set(instrument_name="source", param_name=current_source_param, value=current_source_param_value)

        assert flux_bus.get("awg", sequencer_param) is True
        assert flux_bus.get("source", current_source_param) == current_source_param_value

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute(
        self,
        mock_execute: MagicMock,
        pulse_bus_schedule: PulseBusSchedule,
        sequencer: SequencerQCM,
        current_source: S4gDacChannel,
    ):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        flux_bus = FluxBus(awg=sequencer, source=current_source)
        flux_bus.execute(
            instrument_name="awg",
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
