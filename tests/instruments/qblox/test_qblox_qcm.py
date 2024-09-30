"""Tests for the QbloxQCM class."""

import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.qblox.qblox_pulsar_controller import QbloxPulsarController
from qililab.instruments.qblox import QbloxQCM
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="pulsar_controller_qcm")
def fixture_pulsar_controller_qcm():
    """Return an instance of QbloxPulsarController class"""
    platform = build_platform(runcard=Galadriel.runcard)
    settings = copy.deepcopy(Galadriel.pulsar_controller_qcm_0)
    settings.pop("name")
    return QbloxPulsarController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="qcm_no_device")
def fixture_qcm_no_device():
    """Return an instance of QbloxQCM class"""
    settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    settings.pop("name")
    return QbloxQCM(settings=settings)


@pytest.fixture(name="qcm")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
def fixture_qcm(mock_pulsar: MagicMock, pulsar_controller_qcm: QbloxPulsarController):
    """Return connected instance of QbloxQCM class"""
    # add dynamically created attributes
    mock_instance = mock_pulsar.return_value
    mock_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "sequencer1",
            "out0_offset",
            "out1_offset",
            "out2_offset",
            "out3_offset",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "scope_acq_sequencer_select",
            "disconnect_outputs",
            "disconnect_inputs",
        ]
    )
    mock_instance.sequencers = [mock_instance.sequencer0, mock_instance.sequencer1]
    spec = [
        "sync_en",
        "gain_awg_path0",
        "gain_awg_path1",
        "sequence",
        "mod_en_awg",
        "nco_freq",
        "scope_acq_sequencer_select",
        "channel_map_path0_out0_en",
        "channel_map_path1_out1_en",
        "demod_en_acq",
        "integration_length_acq",
        "set",
        "mixer_corr_phase_offset_degree",
        "mixer_corr_gain_ratio",
        "offset_awg_path0",
        "offset_awg_path1",
        "marker_ovr_en",
        "marker_ovr_value",
        "connect_out0",
        "connect_out1",
    ]
    mock_instance.sequencer0.mock_add_spec(spec)
    mock_instance.sequencer1.mock_add_spec(spec)
    pulsar_controller_qcm.connect()
    return pulsar_controller_qcm.modules[0]


class TestQbloxQCM:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_inital_setup_method(self, qcm: QbloxQCM):
        """Test initial_setup method"""
        qcm.initial_setup()
        qcm.device.out0_offset.assert_called()
        qcm.device.out1_offset.assert_called()
        qcm.device.out2_offset.assert_called()
        qcm.device.out3_offset.assert_called()
        qcm.device.sequencers[0].sync_en.assert_called_with(False)
        qcm.device.sequencers[0].mod_en_awg.assert_called()
        qcm.device.sequencers[0].offset_awg_path0.assert_called()
        qcm.device.sequencers[0].offset_awg_path1.assert_called()
        qcm.device.sequencers[0].mixer_corr_gain_ratio.assert_called()
        qcm.device.sequencers[0].mixer_corr_phase_offset_degree.assert_called()

    def test_start_sequencer_method(self, qcm: QbloxQCM):
        """Test start_sequencer method"""
        qcm.start_sequencer(port="drive_q0")
        qcm.device.arm_sequencer.assert_not_called()
        qcm.device.start_sequencer.assert_not_called()

    @pytest.mark.parametrize(
        "parameter, value, channel_id",
        [
            (Parameter.GAIN, 0.02, 0),
            (Parameter.GAIN_I, 0.03, 0),
            (Parameter.GAIN_Q, 0.01, 0),
            (Parameter.OFFSET_OUT0, 1.234, None),
            (Parameter.OFFSET_OUT1, 0, None),
            (Parameter.OFFSET_OUT2, 0.123, None),
            (Parameter.OFFSET_OUT3, 10, None),
            (Parameter.OFFSET_I, 0.8, 0),
            (Parameter.OFFSET_Q, 0.11, 0),
            (Parameter.IF, 100_000, 0),
            (Parameter.HARDWARE_MODULATION, True, 0),
            (Parameter.HARDWARE_MODULATION, False, 0),
            (Parameter.NUM_BINS, 1, 0),
            (Parameter.GAIN_IMBALANCE, 0.1, 0),
            (Parameter.PHASE_IMBALANCE, 0.09, 0),
        ],
    )
    def test_setup_method(
        self, parameter: Parameter, value: float | bool | int, channel_id: int, qcm: QbloxQCM, qcm_no_device: QbloxQCM
    ):
        """Test setup method"""
        for qcms in [qcm, qcm_no_device]:
            qcms.setup(parameter=parameter, value=value, channel_id=channel_id)
            if parameter == Parameter.GAIN:
                assert qcms.awg_sequencers[channel_id].gain_i == value
                assert qcms.awg_sequencers[channel_id].gain_q == value
            if parameter == Parameter.GAIN_I:
                assert qcms.awg_sequencers[channel_id].gain_i == value
            if parameter == Parameter.GAIN_Q:
                assert qcms.awg_sequencers[channel_id].gain_q == value
            if parameter == Parameter.OFFSET_I:
                assert qcms.awg_sequencers[channel_id].offset_i == value
            if parameter == Parameter.OFFSET_Q:
                assert qcms.awg_sequencers[channel_id].offset_q == value
            if parameter == Parameter.IF:
                assert qcms.awg_sequencers[channel_id].intermediate_frequency == value
            if parameter == Parameter.HARDWARE_MODULATION:
                assert qcms.awg_sequencers[channel_id].hardware_modulation == value
            if parameter == Parameter.NUM_BINS:
                assert qcms.awg_sequencers[channel_id].num_bins == value
            if parameter == Parameter.GAIN_IMBALANCE:
                assert qcms.awg_sequencers[channel_id].gain_imbalance == value
            if parameter == Parameter.PHASE_IMBALANCE:
                assert qcms.awg_sequencers[channel_id].phase_imbalance == value
            if parameter in {
                Parameter.OFFSET_OUT0,
                Parameter.OFFSET_OUT1,
                Parameter.OFFSET_OUT2,
                Parameter.OFFSET_OUT3,
            }:
                output = int(parameter.value[-1])
                assert qcms.out_offsets[output] == value

    @pytest.mark.parametrize(
        "parameter, value, port_id",
        [
            (Parameter.GAIN, 0.02, "drive_q0"),
            (Parameter.GAIN_I, 0.03, "drive_q0"),
            (Parameter.GAIN_Q, 0.01, "drive_q0"),
            (Parameter.OFFSET_OUT0, 1.234, None),
            (Parameter.OFFSET_OUT1, 0, None),
            (Parameter.OFFSET_OUT2, 0.123, None),
            (Parameter.OFFSET_OUT3, 10, None),
            (Parameter.OFFSET_I, 0.8, "drive_q0"),
            (Parameter.OFFSET_Q, 0.11, "drive_q0"),
            (Parameter.IF, 100_000, "drive_q0"),
            (Parameter.HARDWARE_MODULATION, True, "drive_q0"),
            (Parameter.HARDWARE_MODULATION, False, "drive_q0"),
            (Parameter.NUM_BINS, 1, "drive_q0"),
            (Parameter.GAIN_IMBALANCE, 0.1, "drive_q0"),
            (Parameter.PHASE_IMBALANCE, 0.09, "drive_q0"),
        ],
    )
    def test_setup_method_with_port_id(
        self,
        parameter: Parameter,
        value: float | bool | int,
        port_id: str | None,
        qcm: QbloxQCM,
        qcm_no_device: QbloxQCM,
    ):
        """Test setup method"""
        for qcms in [qcm, qcm_no_device]:
            if port_id is not None:
                channel_id = qcms.get_sequencers_from_chip_port_id(port_id)[0].identifier
            else:
                channel_id = None
            qcms.setup(parameter=parameter, value=value, channel_id=channel_id)
            if parameter == Parameter.GAIN:
                assert qcms.awg_sequencers[channel_id].gain_i == value
                assert qcms.awg_sequencers[channel_id].gain_q == value
            if parameter == Parameter.GAIN_I:
                assert qcms.awg_sequencers[channel_id].gain_i == value
            if parameter == Parameter.GAIN_Q:
                assert qcms.awg_sequencers[channel_id].gain_q == value
            if parameter == Parameter.OFFSET_I:
                assert qcms.awg_sequencers[channel_id].offset_i == value
            if parameter == Parameter.OFFSET_Q:
                assert qcms.awg_sequencers[channel_id].offset_q == value
            if parameter == Parameter.IF:
                assert qcms.awg_sequencers[channel_id].intermediate_frequency == value
            if parameter == Parameter.HARDWARE_MODULATION:
                assert qcms.awg_sequencers[channel_id].hardware_modulation == value
            if parameter == Parameter.NUM_BINS:
                assert qcms.awg_sequencers[channel_id].num_bins == value
            if parameter == Parameter.GAIN_IMBALANCE:
                assert qcms.awg_sequencers[channel_id].gain_imbalance == value
            if parameter == Parameter.PHASE_IMBALANCE:
                assert qcms.awg_sequencers[channel_id].phase_imbalance == value
            if parameter in {
                Parameter.OFFSET_OUT0,
                Parameter.OFFSET_OUT1,
                Parameter.OFFSET_OUT2,
                Parameter.OFFSET_OUT3,
            }:
                output = int(parameter.value[-1])
                assert qcms.out_offsets[output] == value

    def test_setup_out_offset_raises_error(self, qcm: QbloxQCM):
        """Test that calling ``_set_out_offset`` with a wrong output value raises an error."""
        with pytest.raises(IndexError, match="Output 5 is out of range"):
            qcm._set_out_offset(output=5, value=1)

    def test_turn_off_method(self, qcm: QbloxQCM):
        """Test turn_off method"""
        qcm.turn_off()
        assert qcm.device.stop_sequencer.call_count == qcm.num_sequencers

    def test_name_property(self, qcm_no_device: QbloxQCM):
        """Test name property."""
        assert qcm_no_device.name == InstrumentName.QBLOX_QCM

    def test_firmware_property(self, qcm_no_device: QbloxQCM):
        """Test firmware property."""
        assert qcm_no_device.firmware == qcm_no_device.settings.firmware
