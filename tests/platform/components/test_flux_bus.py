"""Unittests for the FluxBus class"""
from unittest.mock import MagicMock, patch

import pytest
from qblox_instruments.native.spi_rack_modules import DummyD5aApi, DummyS4gApi
from qcodes import Instrument
from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyChannel

from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.spi_rack import D5aDacChannel, S4gDacChannel
from qililab.drivers.interfaces import CurrentSource, VoltageSource
from qililab.platform.components import BusDriver, FluxBus
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

    return PulseBusSchedule(timeline=timeline, port="test")


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
    return FluxBus(alias=ALIAS, port=PORT, awg=sequencer, source=current_source, distortions=[])


@pytest.fixture(name="flux_bus_voltage_source")
def fixture_flux_bus_voltage_source(sequencer: SequencerQCM, voltage_source: D5aDacChannel) -> FluxBus:
    """Return FluxBus instance with voltage source."""
    return FluxBus(alias=ALIAS, port=PORT, awg=sequencer, source=voltage_source, distortions=[])


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
            + "".join(f"--|{instrument.alias}|" for instrument in flux_bus_current_source.instruments.values())
            + f"--> port {flux_bus_current_source.port}"
        )

        assert str(flux_bus_current_source) == expected_str


# Instrument parameters for testing:
PATH0_OUT = 0
PATH1_OUT = 1
INTERMED_FREQ = 100e5
GAIN = 0.9
SOURCE_ALIAS = "test"
AWG_ALIAS = "q0_readout"


@pytest.fixture(name="current_source_api")
def fixture_current_source_api() -> S4gDacChannel:
    """Return a S4gDacChannel instance."""
    mocked_parent = MagicMock()
    mocked_parent.api = DummyS4gApi(spi_rack=MagicMock(), module=0)
    return S4gDacChannel(parent=mocked_parent, name=SOURCE_ALIAS, dac=0)


@pytest.fixture(name="voltage_source_api")
def fixture_voltage_source_api() -> D5aDacChannel:
    """Return a D5aDacChannel instance."""
    mocked_parent = MagicMock()
    mocked_parent.api = DummyD5aApi(spi_rack=MagicMock(), module=0)
    return D5aDacChannel(parent=mocked_parent, name=SOURCE_ALIAS, dac=0)


@pytest.fixture(name="sequencer_qcm")
def fixture_sequencer_qcm() -> SequencerQCM:
    """Return a SequencerQCM instance."""
    sequencer = SequencerQCM(parent=MagicMock(), name=AWG_ALIAS, seq_idx=0)
    sequencer.add_parameter(name="path0_out", vals=vals.Ints(), set_cmd=None, initial_value=PATH0_OUT)
    sequencer.add_parameter(name="path1_out", vals=vals.Ints(), set_cmd=None, initial_value=PATH1_OUT)
    sequencer.add_parameter(
        name="intermediate_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=INTERMED_FREQ
    )
    sequencer.add_parameter(name="gain", vals=vals.Numbers(), set_cmd=None, initial_value=GAIN)
    return sequencer


@pytest.fixture(name="current_flux_bus_instruments")
def fixture_current_flux_bus_instruments(sequencer_qcm: SequencerQCM, current_source_api: S4gDacChannel) -> list:
    """Return a list of instrument instances."""
    return [sequencer_qcm, current_source_api]


@pytest.fixture(name="current_flux_bus_dictionary")
def fixture_current_flux_bus_dictionary() -> dict:
    """Returns a dictionary of a FluxBus (current) instance."""
    return {
        "alias": ALIAS,
        "type": "FluxBus",
        "AWG": {
            "alias": AWG_ALIAS,
            "parameters": {
                "path0_out": PATH0_OUT,
                "path1_out": PATH1_OUT,
                "intermediate_frequency": INTERMED_FREQ,
                "gain": GAIN,
            },
        },
        "CurrentSource": {
            "alias": SOURCE_ALIAS,
        },
        "port": PORT,
        "distortions": [],
    }


class TestCurrentFluxBusSerialization:
    """Unit tests checking the FluxBus (voltage) serialization methods."""

    def test_from_dict(
        self,
        current_flux_bus_dictionary: dict,
        current_flux_bus_instruments: list,
        sequencer_qcm: SequencerQCM,
        current_source_api: S4gDacChannel,
    ):
        """Test that the from_dict method of the FluxBus class (current) works correctly."""
        with patch("qcodes.instrument.instrument_base.InstrumentBase.set") as mock_set:
            flux_bus = BusDriver.from_dict(current_flux_bus_dictionary, current_flux_bus_instruments)

            # Check the basic bus dictionary part
            assert isinstance(flux_bus, FluxBus)
            assert flux_bus.alias == ALIAS
            assert flux_bus.port == PORT
            assert flux_bus.distortions == []

            # Check the instrument parameters dictionary part inside the bus dictionary
            assert mock_set.call_count == 4

            assert flux_bus.instruments["awg"] == sequencer_qcm
            for param, value in current_flux_bus_dictionary["AWG"]["parameters"].items():
                assert param in flux_bus.instruments["awg"].params
                mock_set.assert_any_call(param, value)

            assert flux_bus.instruments["source"] == current_source_api
            assert "parameters" not in current_flux_bus_dictionary["CurrentSource"]
            # This test that the attenuator has no parameters

    def test_to_dict(self, sequencer_qcm: SequencerQCM, current_source_api: S4gDacChannel):
        # sourcery skip: merge-duplicate-blocks, remove-redundant-if, switch
        """Test that the to_dict method of the FluxBus class (current) has the correct structure."""
        bus = FluxBus(
            alias=ALIAS,
            port=PORT,
            awg=sequencer_qcm,
            source=current_source_api,
            distortions=[],
        )
        # patch the values to True, we are only interested in the structure of the dictionary
        with patch("qcodes.instrument.instrument_base.InstrumentBase.get", return_value=True) as mock_get:
            dictionary = bus.to_dict()
            mock_get.assert_called()

            assert dictionary == {
                "alias": ALIAS,
                "type": "FluxBus",
                "AWG": {
                    "alias": AWG_ALIAS,
                    "parameters": {
                        "channel_map_path0_out0_en": True,
                        "channel_map_path1_out1_en": True,
                        "channel_map_path0_out2_en": True,
                        "channel_map_path1_out3_en": True,
                        "sync_en": True,
                        "nco_freq": True,
                        "nco_phase_offs": True,
                        "nco_prop_delay_comp": True,
                        "nco_prop_delay_comp_en": True,
                        "marker_ovr_en": True,
                        "marker_ovr_value": True,
                        "trigger1_count_threshold": True,
                        "trigger1_threshold_invert": True,
                        "trigger2_count_threshold": True,
                        "trigger2_threshold_invert": True,
                        "trigger3_count_threshold": True,
                        "trigger3_threshold_invert": True,
                        "trigger4_count_threshold": True,
                        "trigger4_threshold_invert": True,
                        "trigger5_count_threshold": True,
                        "trigger5_threshold_invert": True,
                        "trigger6_count_threshold": True,
                        "trigger6_threshold_invert": True,
                        "trigger7_count_threshold": True,
                        "trigger7_threshold_invert": True,
                        "trigger8_count_threshold": True,
                        "trigger8_threshold_invert": True,
                        "trigger9_count_threshold": True,
                        "trigger9_threshold_invert": True,
                        "trigger10_count_threshold": True,
                        "trigger10_threshold_invert": True,
                        "trigger11_count_threshold": True,
                        "trigger11_threshold_invert": True,
                        "trigger12_count_threshold": True,
                        "trigger12_threshold_invert": True,
                        "trigger13_count_threshold": True,
                        "trigger13_threshold_invert": True,
                        "trigger14_count_threshold": True,
                        "trigger14_threshold_invert": True,
                        "trigger15_count_threshold": True,
                        "trigger15_threshold_invert": True,
                        "cont_mode_en_awg_path0": True,
                        "cont_mode_en_awg_path1": True,
                        "cont_mode_waveform_idx_awg_path0": True,
                        "cont_mode_waveform_idx_awg_path1": True,
                        "upsample_rate_awg_path0": True,
                        "upsample_rate_awg_path1": True,
                        "gain_awg_path0": True,
                        "gain_awg_path1": True,
                        "offset_awg_path0": True,
                        "offset_awg_path1": True,
                        "mixer_corr_phase_offset_degree": True,
                        "mixer_corr_gain_ratio": True,
                        "mod_en_awg": True,
                        "demod_en_acq": True,
                        "integration_length_acq": True,
                        "thresholded_acq_rotation": True,
                        "thresholded_acq_threshold": True,
                        "thresholded_acq_marker_en": True,
                        "thresholded_acq_marker_address": True,
                        "thresholded_acq_marker_invert": True,
                        "thresholded_acq_trigger_en": True,
                        "thresholded_acq_trigger_address": True,
                        "thresholded_acq_trigger_invert": True,
                        "swap_paths": True,
                        "path0_out": True,
                        "path1_out": True,
                        "intermediate_frequency": True,
                        "gain": True,
                    },
                },
                "CurrentSource": {
                    "alias": SOURCE_ALIAS,
                    "parameters": {
                        "current": True,
                        "span": True,
                        "ramp_rate": True,
                        "ramp_max_step": True,
                        "ramping_enabled": True,
                        "is_ramping": True,
                        "stepsize": True,
                        "dac_channel": True,
                    },
                },
                "port": PORT,
                "distortions": [],
            }


@pytest.fixture(name="voltage_flux_bus_instruments")
def fixture_voltage_flux_bus_instruments(sequencer_qcm: SequencerQCM, voltage_source_api: D5aDacChannel) -> list:
    """Return a list of instrument instances."""
    return [sequencer_qcm, voltage_source_api]


@pytest.fixture(name="voltage_flux_bus_dictionary")
def fixture_voltage_flux_bus_dictionary() -> dict:
    """Returns a dictionary of a FluxBus (current) instance."""
    return {
        "alias": ALIAS,
        "type": "FluxBus",
        "AWG": {
            "alias": AWG_ALIAS,
            "parameters": {
                "path0_out": PATH0_OUT,
                "path1_out": PATH1_OUT,
                "intermediate_frequency": INTERMED_FREQ,
                "gain": GAIN,
            },
        },
        "VoltageSource": {
            "alias": SOURCE_ALIAS,
        },
        "port": PORT,
        "distortions": [],
    }


class TestVoltageFluxBusSerialization:
    """Unit tests checking the FluxBus (voltage) serialization methods."""

    def test_from_dict(
        self,
        voltage_flux_bus_dictionary: dict,
        voltage_flux_bus_instruments: list,
        sequencer_qcm: SequencerQCM,
        voltage_source_api: D5aDacChannel,
    ):
        """Test that the from_dict method of the FluxBus class (voltage) works correctly."""
        with patch("qcodes.instrument.instrument_base.InstrumentBase.set") as mock_set:
            flux_bus = BusDriver.from_dict(voltage_flux_bus_dictionary, voltage_flux_bus_instruments)

            # Check the basic bus dictionary part
            assert isinstance(flux_bus, FluxBus)
            assert flux_bus.alias == ALIAS
            assert flux_bus.port == PORT
            assert flux_bus.distortions == []

            # Check the instrument parameters dictionary part inside the bus dictionary
            assert mock_set.call_count == 4

            assert flux_bus.instruments["awg"] == sequencer_qcm
            for param, value in voltage_flux_bus_dictionary["AWG"]["parameters"].items():
                assert param in flux_bus.instruments["awg"].params
                mock_set.assert_any_call(param, value)

            assert flux_bus.instruments["source"] == voltage_source_api
            assert "parameters" not in voltage_flux_bus_dictionary["VoltageSource"]
            # This test that the attenuator has no parameters

    def test_to_dict(self, sequencer_qcm: SequencerQCM, voltage_source_api: D5aDacChannel):
        # sourcery skip: merge-duplicate-blocks, remove-redundant-if, switch
        """Test that the to_dict method of the FluxBus class (voltage) has the correct structure."""
        bus = FluxBus(
            alias=ALIAS,
            port=PORT,
            awg=sequencer_qcm,
            source=voltage_source_api,
            distortions=[],
        )
        # patch the values to True, we are only interested in the structure of the dictionary
        with patch("qcodes.instrument.instrument_base.InstrumentBase.get", return_value=True) as mock_get:
            dictionary = bus.to_dict()
            mock_get.assert_called()

            assert dictionary == {
                "alias": ALIAS,
                "type": "FluxBus",
                "AWG": {
                    "alias": AWG_ALIAS,
                    "parameters": {
                        "channel_map_path0_out0_en": True,
                        "channel_map_path1_out1_en": True,
                        "channel_map_path0_out2_en": True,
                        "channel_map_path1_out3_en": True,
                        "sync_en": True,
                        "nco_freq": True,
                        "nco_phase_offs": True,
                        "nco_prop_delay_comp": True,
                        "nco_prop_delay_comp_en": True,
                        "marker_ovr_en": True,
                        "marker_ovr_value": True,
                        "trigger1_count_threshold": True,
                        "trigger1_threshold_invert": True,
                        "trigger2_count_threshold": True,
                        "trigger2_threshold_invert": True,
                        "trigger3_count_threshold": True,
                        "trigger3_threshold_invert": True,
                        "trigger4_count_threshold": True,
                        "trigger4_threshold_invert": True,
                        "trigger5_count_threshold": True,
                        "trigger5_threshold_invert": True,
                        "trigger6_count_threshold": True,
                        "trigger6_threshold_invert": True,
                        "trigger7_count_threshold": True,
                        "trigger7_threshold_invert": True,
                        "trigger8_count_threshold": True,
                        "trigger8_threshold_invert": True,
                        "trigger9_count_threshold": True,
                        "trigger9_threshold_invert": True,
                        "trigger10_count_threshold": True,
                        "trigger10_threshold_invert": True,
                        "trigger11_count_threshold": True,
                        "trigger11_threshold_invert": True,
                        "trigger12_count_threshold": True,
                        "trigger12_threshold_invert": True,
                        "trigger13_count_threshold": True,
                        "trigger13_threshold_invert": True,
                        "trigger14_count_threshold": True,
                        "trigger14_threshold_invert": True,
                        "trigger15_count_threshold": True,
                        "trigger15_threshold_invert": True,
                        "cont_mode_en_awg_path0": True,
                        "cont_mode_en_awg_path1": True,
                        "cont_mode_waveform_idx_awg_path0": True,
                        "cont_mode_waveform_idx_awg_path1": True,
                        "upsample_rate_awg_path0": True,
                        "upsample_rate_awg_path1": True,
                        "gain_awg_path0": True,
                        "gain_awg_path1": True,
                        "offset_awg_path0": True,
                        "offset_awg_path1": True,
                        "mixer_corr_phase_offset_degree": True,
                        "mixer_corr_gain_ratio": True,
                        "mod_en_awg": True,
                        "demod_en_acq": True,
                        "integration_length_acq": True,
                        "thresholded_acq_rotation": True,
                        "thresholded_acq_threshold": True,
                        "thresholded_acq_marker_en": True,
                        "thresholded_acq_marker_address": True,
                        "thresholded_acq_marker_invert": True,
                        "thresholded_acq_trigger_en": True,
                        "thresholded_acq_trigger_address": True,
                        "thresholded_acq_trigger_invert": True,
                        "swap_paths": True,
                        "path0_out": True,
                        "path1_out": True,
                        "intermediate_frequency": True,
                        "gain": True,
                    },
                },
                "VoltageSource": {
                    "alias": SOURCE_ALIAS,
                    "parameters": {
                        "voltage": True,
                        "span": True,
                        "ramp_rate": True,
                        "ramp_max_step": True,
                        "ramping_enabled": True,
                        "is_ramping": True,
                        "stepsize": True,
                        "dac_channel": True,
                    },
                },
                "port": PORT,
                "distortions": [],
            }
