"""Unittest for DriveBus class"""
from unittest.mock import MagicMock, patch

import pytest
import qcodes.validators as vals
from qcodes import Instrument
from qcodes.instrument import DelegateParameter
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers import parameters
from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.platform.components import BusDriver, DriveBus
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
ALIAS = "drivebus_0"


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


class MockQcmQrmRF(DummyInstrument):  # pylint: disable=abstract-method
    """Mocks the QcmQrmRF class."""

    def __init__(self, name, qcm_qrm, parent=None, slot_idx=0):  # pylint: disable=unused-argument
        """Init function"""
        super().__init__(name=name, gates=["dac1"])

        channels = ["out0", "out1"]
        for channel in channels:
            # local oscillator parameters
            self.add_parameter(
                name=f"{channel}_lo_freq",
                label="Frequency",
                unit="Hz",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )
            self.add_parameter(
                f"{channel}_lo_en",
                label="Status",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )
            # attenuator parameters
            self.add_parameter(
                name=f"{channel}_att",
                label="Attenuation",
                unit="dB",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )

    def __str__(self):
        return "MockQcmQrmRF"


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return get_pulse_bus_schedule(start_time=0)


@pytest.fixture(name="sequencer")
def fixture_sequencer() -> SequencerQCM:
    """Return SequencerQCM instance."""
    return SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)


@pytest.fixture(name="local_oscillator")
def fixture_local_oscillator() -> QcmQrmRfLo:
    """Return QcmQrmRfLo instance"""
    channel = "out0"
    lo_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm="qcm")

    return QcmQrmRfLo(name=f"test_lo_{channel}", parent=lo_parent, channel=channel)


@pytest.fixture(name="attenuator")
def fixture_attenuator() -> QcmQrmRfAtt:
    """Return QcmQrmRfAtt instance"""
    channel = "out1"
    att_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm="qcm")
    attenuator = QcmQrmRfAtt(name=f"test_att_{channel}", parent=att_parent, channel=channel)
    # duplicated parameter for testing purposes
    attenuator.add_parameter(
        "status",
        label="Delegated parameter device status",
        source=att_parent.parameters[f"{channel}_lo_en"],
        parameter_class=DelegateParameter,
    )
    return attenuator


@pytest.fixture(name="drive_bus")
def fixture_drive_bus(sequencer: SequencerQCM, local_oscillator: QcmQrmRfLo, attenuator: QcmQrmRfAtt) -> DriveBus:
    """Return DriveBus instance."""
    return DriveBus(
        alias=ALIAS, port=PORT, awg=sequencer, local_oscillator=local_oscillator, attenuator=attenuator, distortions=[]
    )


class TestDriveBus:
    """Unit tests checking the DriveBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""
        Instrument.close_all()

    def test_init(self, drive_bus: DriveBus):
        """Test init method"""
        assert drive_bus.alias == ALIAS
        assert drive_bus.port == PORT
        assert isinstance(drive_bus.instruments["awg"], SequencerQCM)
        assert isinstance(drive_bus.instruments["local_oscillator"], QcmQrmRfLo)
        assert isinstance(drive_bus.instruments["attenuator"], QcmQrmRfAtt)

    def test_set(self, drive_bus: DriveBus):
        """Test set method"""
        # Testing with parameters that exists
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation
        drive_bus.set(param_name=sequencer_param, value=True)
        drive_bus.set(param_name=lo_frequency_param, value=2)
        drive_bus.set(param_name=attenuation_param, value=2)

        assert drive_bus.instruments["awg"].get(sequencer_param) is True
        assert drive_bus.instruments["local_oscillator"].get(lo_frequency_param) == 2
        assert drive_bus.instruments["attenuator"].get(attenuation_param) == 2

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            drive_bus.set(param_name=random_param, value=True)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            drive_bus.set(param_name=duplicated_param, value=True)

    def test_get(self, drive_bus: DriveBus):
        """Test get method"""
        # Testing with parameters that exists
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation
        drive_bus.set(param_name=sequencer_param, value=True)
        drive_bus.set(param_name=lo_frequency_param, value=2)
        drive_bus.set(param_name=attenuation_param, value=2)

        assert drive_bus.get(sequencer_param) is True
        assert drive_bus.get(lo_frequency_param) == 2
        assert drive_bus.get(attenuation_param) == 2

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            drive_bus.get(param_name=random_param)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            drive_bus.get(param_name=duplicated_param)

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute(self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, drive_bus: DriveBus):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        drive_bus.execute(
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

    def test_str(self, drive_bus: DriveBus):
        """Unittest for __str__ method."""
        expected_str = (
            f"{ALIAS} ({drive_bus.__class__.__name__}): "
            + "".join(f"--|{instrument.alias}|" for instrument in drive_bus.instruments.values())
            + f"--> port {drive_bus.port}"
        )

        assert str(drive_bus) == expected_str


# Instrument parameters for testing:
PATH0_OUT = 0
PATH1_OUT = 1
INTERMED_FREQ = 100e5
GAIN = 0.9
LO_FREQUENCY = 1e9
ATTENUATION = 20
ATT_ALIAS = "attenuator_0"
LO_ALIAS = "lo_readout"
AWG_ALIAS = "q0_readout"


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


@pytest.fixture(name="qcmqrm_lo")
def fixture_qcmqrm_lo() -> QcmQrmRfLo:
    """Return a QcmQrmRfLo instance."""
    return QcmQrmRfLo(parent=MagicMock(), name=LO_ALIAS, channel="test")


@pytest.fixture(name="qcmqrm_att")
def fixture_qcmqrm_att() -> QcmQrmRfAtt:
    """Return a QcmQrmRfAtt instance."""
    attenuator = QcmQrmRfAtt(parent=MagicMock(), name=ATT_ALIAS, channel="test")
    attenuator.add_parameter(name="lo_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=LO_FREQUENCY)
    return attenuator


@pytest.fixture(name="drive_bus_instruments")
def fixture_drive_bus_instruments(sequencer_qcm: SequencerQCM, qcmqrm_lo: QcmQrmRfLo, qcmqrm_att: QcmQrmRfAtt) -> list:
    """Return a list of instrument instances."""
    return [sequencer_qcm, qcmqrm_lo, qcmqrm_att]


@pytest.fixture(name="drive_bus_dictionary")
def fixture_drive_bus_dictionary() -> dict:
    """Returns a dictionary of a DriveBus instance."""
    return {
        "alias": ALIAS,
        "type": "DriveBus",
        "AWG": {
            "alias": AWG_ALIAS,
            "parameters": {
                "path0_out": PATH0_OUT,
                "path1_out": PATH1_OUT,
                "intermediate_frequency": INTERMED_FREQ,
                "gain": GAIN,
            },
        },
        "LocalOscillator": {
            "alias": LO_ALIAS,
        },
        "Attenuator": {
            "alias": ATT_ALIAS,
            "parameters": {
                "lo_frequency": LO_FREQUENCY,
            },
        },
        "port": PORT,
        "distortions": [],
    }


class TestDriveBusSerialization:
    """Unit tests checking the DriveBus serialization methods."""

    def test_from_dict(
        self,
        drive_bus_dictionary: dict,
        drive_bus_instruments: list,
        sequencer_qcm: SequencerQCM,
        qcmqrm_lo: QcmQrmRfLo,
        qcmqrm_att: QcmQrmRfAtt,
    ):
        """Test that the from_dict method of the DriveBus class works correctly."""
        with patch("qcodes.instrument.instrument_base.InstrumentBase.set") as mock_set:
            drive_bus = BusDriver.from_dict(drive_bus_dictionary, drive_bus_instruments)

            # Check the basic bus dictionary part
            assert isinstance(drive_bus, DriveBus)
            assert drive_bus.alias == ALIAS
            assert drive_bus.port == PORT
            assert drive_bus.distortions == []

            # Check the instrument parameters dictionary part inside the bus dictionary
            assert mock_set.call_count == 5

            assert drive_bus.instruments["awg"] == sequencer_qcm
            for param, value in drive_bus_dictionary["AWG"]["parameters"].items():
                assert param in drive_bus.instruments["awg"].params
                mock_set.assert_any_call(param, value)

            assert drive_bus.instruments["attenuator"] == qcmqrm_att
            for param, value in drive_bus_dictionary["Attenuator"]["parameters"].items():
                assert param in drive_bus.instruments["attenuator"].params
                mock_set.assert_any_call(param, value)

            assert drive_bus.instruments["local_oscillator"] == qcmqrm_lo
            assert "parameters" not in drive_bus_dictionary["LocalOscillator"]
            # This test that the local_oscillator has no set parameters by us

    def test_to_dict(self, sequencer_qcm: SequencerQCM, qcmqrm_lo: QcmQrmRfLo, qcmqrm_att: QcmQrmRfAtt):
        # sourcery skip: merge-duplicate-blocks, remove-redundant-if, switch
        """Test that the to_dict method of the DriveBus class has the correct structure."""
        bus = DriveBus(
            alias=ALIAS,
            port=PORT,
            awg=sequencer_qcm,
            local_oscillator=qcmqrm_lo,
            attenuator=qcmqrm_att,
            distortions=[],
        )
        # patch the values to True, we are only interested in the structure of the dictionary
        with patch("qcodes.instrument.instrument_base.InstrumentBase.get", return_value=True) as mock_get:
            dictionary = bus.to_dict()
            mock_get.assert_called()

            assert dictionary == {
                "alias": ALIAS,
                "type": "DriveBus",
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
                "LocalOscillator": {
                    "alias": LO_ALIAS,
                    "parameters": {"lo_frequency": True, "status": True},
                },
                "Attenuator": {
                    "alias": ATT_ALIAS,
                    "parameters": {
                        "attenuation": True,
                        "lo_frequency": True,
                    },
                },
                "port": PORT,
                "distortions": [],
            }
