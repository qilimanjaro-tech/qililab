"""Tests for the Qblox Module class."""

from typing import cast
from unittest.mock import MagicMock

import pytest
from qblox_instruments.qcodes_drivers.module import Module as QcmQrm
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.data_management import build_platform
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxQCMRF
from qililab.platform import Platform
from qililab.typings import Parameter

MAX_ATTENUATION = 30


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard="tests/instruments/qblox/qblox_runcard.yaml")


@pytest.fixture(name="qcm_rf")
def fixture_qrm(platform: Platform):
    qcm_rf = cast(QbloxQCMRF, platform.get_element(alias="qcm-rf"))

    sequencer_mock_spec = [
        *Sequencer._get_required_parent_attr_names(),
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
        "mixer_corr_phase_offset_degree",
        "mixer_corr_gain_ratio",
        "connect_out0",
        "connect_out1",
        "connect_out2",
        "connect_out3",
        "marker_ovr_en",
        "offset_awg_path0",
        "offset_awg_path1",
    ]

    module_mock_spec = [
        *QcmQrm._get_required_parent_qtm_attr_names(),
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
        "sequencers",
        "scope_acq_sequencer_select",
        "get_acquisitions",
        "disconnect_outputs",
        "disconnect_inputs",
        "arm_sequencer",
        "start_sequencer",
        "reset",
        "set",
        "out0_lo_freq_cal_type_default",
        "out1_lo_freq_cal_type_default",
    ]

    # Create a mock device using create_autospec to follow the interface of the expected device
    qcm_rf.device = MagicMock()
    qcm_rf.device.mock_add_spec(module_mock_spec)
    qcm_rf.device._get_max_out_att_0 = MagicMock(return_value=MAX_ATTENUATION)
    qcm_rf.device._get_max_out_att_1 = MagicMock(return_value=MAX_ATTENUATION)
    qcm_rf.device._run_mixer_lo_calib = MagicMock()

    qcm_rf.device.sequencers = {0: MagicMock(), 1: MagicMock()}

    for sequencer in qcm_rf.device.sequencers:
        qcm_rf.device.sequencers[sequencer].mock_add_spec(sequencer_mock_spec)
        qcm_rf.device.sequencers[sequencer].sideband_cal = MagicMock()

    return qcm_rf


class TestQbloxQCMRF:
    def test_init(self, qcm_rf: QbloxQCMRF):
        assert qcm_rf.alias == "qcm-rf"
        assert len(qcm_rf.awg_sequencers) == 2

    @pytest.mark.parametrize(
        "parameter, value",
        [
            # Test GAIN setting
            (Parameter.GAIN, 2.0),
            (Parameter.GAIN, 3.5),
            # Test GAIN_I and GAIN_Q settings
            (Parameter.GAIN_I, 1.5),
            (Parameter.GAIN_Q, 1.5),
            # Test OFFSET_I and OFFSET_Q settings
            (Parameter.OFFSET_I, 0.1),
            (Parameter.OFFSET_Q, 0.2),
            # Test IF setting (intermediate frequency)
            (Parameter.IF, 100e6),
            # Test HARDWARE_MODULATION setting
            (Parameter.HARDWARE_MODULATION, True),
            # Test GAIN_IMBALANCE setting
            (Parameter.GAIN_IMBALANCE, 0.05),
            # Test PHASE_IMBALANCE setting
            (Parameter.PHASE_IMBALANCE, 0.02),
            # QCM-RF specific
            (Parameter.LO_FREQUENCY, 5e9),
            (Parameter.OUT0_LO_FREQ, 5e9),
            (Parameter.OUT0_LO_EN, True),
            (Parameter.OUT0_ATT, 5),
            (Parameter.OUT0_OFFSET_PATH0, 0.5),
            (Parameter.OUT0_OFFSET_PATH1, 0.5),
            (Parameter.OUT1_LO_FREQ, 6e9),
            (Parameter.OUT1_LO_EN, True),
            (Parameter.OUT1_ATT, 6),
            (Parameter.OUT1_OFFSET_PATH0, 0.6),
            (Parameter.OUT1_OFFSET_PATH1, 0.6),
        ],
    )
    def test_set_parameter(self, qcm_rf: QbloxQCMRF, parameter, value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        qcm_rf.set_parameter(parameter, value, channel_id=0)
        sequencer = qcm_rf.get_sequencer(0)

        # Check values based on the parameter
        if parameter == Parameter.GAIN:
            assert sequencer.gain_i == value
            assert sequencer.gain_q == value
        elif parameter == Parameter.GAIN_I:
            assert sequencer.gain_i == value
        elif parameter == Parameter.GAIN_Q:
            assert sequencer.gain_q == value
        elif parameter == Parameter.OFFSET_I:
            assert sequencer.offset_i == value
        elif parameter == Parameter.OFFSET_Q:
            assert sequencer.offset_q == value
        elif parameter == Parameter.IF:
            assert sequencer.intermediate_frequency == value
        elif parameter == Parameter.HARDWARE_MODULATION:
            assert sequencer.hardware_modulation == value
        elif parameter == Parameter.GAIN_IMBALANCE:
            assert sequencer.gain_imbalance == value
        elif parameter == Parameter.PHASE_IMBALANCE:
            assert sequencer.phase_imbalance == value
        elif parameter == Parameter.LO_FREQUENCY:
            assert qcm_rf.settings.out0_lo_freq == value
        elif parameter == Parameter.OUT0_LO_FREQ:
            assert qcm_rf.settings.out0_lo_freq == value
        elif parameter == Parameter.OUT0_LO_EN:
            assert qcm_rf.settings.out0_lo_en == value
        elif parameter == Parameter.OUT0_ATT:
            assert qcm_rf.settings.out0_att == value
        elif parameter == Parameter.OUT0_OFFSET_PATH0:
            assert qcm_rf.settings.out0_offset_path0 == value
        elif parameter == Parameter.OUT0_OFFSET_PATH1:
            assert qcm_rf.settings.out0_offset_path1 == value
        elif parameter == Parameter.OUT1_LO_FREQ:
            assert qcm_rf.settings.out1_lo_freq == value
        elif parameter == Parameter.OUT1_LO_EN:
            assert qcm_rf.settings.out1_lo_en == value
        elif parameter == Parameter.OUT1_ATT:
            assert qcm_rf.settings.out1_att == value
        elif parameter == Parameter.OUT1_OFFSET_PATH0:
            assert qcm_rf.settings.out1_offset_path0 == value
        elif parameter == Parameter.OUT1_OFFSET_PATH1:
            assert qcm_rf.settings.out1_offset_path1 == value

    def test_set_parameter_raises_error(self, qcm_rf: QbloxQCMRF):
        """Test setting parameters for QCM sequencers."""
        with pytest.raises(ParameterNotFound):
            qcm_rf.set_parameter(Parameter.BUS_FREQUENCY, value=42, channel_id=0)

        with pytest.raises(Exception):
            qcm_rf.set_parameter(Parameter.LO_FREQUENCY, value=5e9, channel_id=None)

        with pytest.raises(Exception):
            qcm_rf.set_parameter(Parameter.OUT0_ATT, value=MAX_ATTENUATION + 10, channel_id=None)

        with pytest.raises(Exception):
            qcm_rf.set_parameter(Parameter.OUT1_ATT, value=MAX_ATTENUATION + 10, channel_id=None)

    @pytest.mark.parametrize(
        "parameter, expected_value",
        [
            # Test GAIN_I and GAIN_Q settings
            (Parameter.GAIN_I, 1.0),
            (Parameter.GAIN_Q, 1.0),
            # Test OFFSET_I and OFFSET_Q settings
            (Parameter.OFFSET_I, 0.0),
            (Parameter.OFFSET_Q, 0.0),
            # Test IF setting (intermediate frequency)
            (Parameter.IF, 100e6),
            # Test HARDWARE_MODULATION setting
            (Parameter.HARDWARE_MODULATION, True),
            # Test GAIN_IMBALANCE setting
            (Parameter.GAIN_IMBALANCE, 0.05),
            # Test PHASE_IMBALANCE setting
            (Parameter.PHASE_IMBALANCE, 0.02),
            # QCM-RF specific
            (Parameter.LO_FREQUENCY, 3e9),  # Same as OUT0_LO_FREQ since we test for channel=0
            (Parameter.OUT0_LO_FREQ, 3e9),
            (Parameter.OUT0_LO_EN, True),
            (Parameter.OUT0_ATT, 10),
            (Parameter.OUT0_OFFSET_PATH0, 0.2),
            (Parameter.OUT0_OFFSET_PATH1, 0.07),
            (Parameter.OUT1_LO_FREQ, 4e9),
            (Parameter.OUT1_LO_EN, True),
            (Parameter.OUT1_ATT, 6),
            (Parameter.OUT1_OFFSET_PATH0, 0.1),
            (Parameter.OUT1_OFFSET_PATH1, 0.6),
        ],
    )
    def test_get_parameter(self, qcm_rf: QbloxQCMRF, parameter, expected_value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        value = qcm_rf.get_parameter(parameter, channel_id=0)
        assert value == expected_value

    def test_get_parameter_raises_error(self, qcm_rf: QbloxQCMRF):
        """Test setting parameters for QCM sequencers using parameterized values."""
        with pytest.raises(ParameterNotFound):
            qcm_rf.get_parameter(Parameter.BUS_FREQUENCY, channel_id=0)

        with pytest.raises(Exception):
            qcm_rf.get_parameter(Parameter.LO_FREQUENCY, channel_id=None)

    @pytest.mark.parametrize(
        "channel_id, expected_error",
        [
            (0, None),  # Valid channel ID
            (5, Exception),  # Invalid channel ID
        ],
    )
    def test_invalid_channel(self, qcm_rf: QbloxQCMRF, channel_id, expected_error):
        """Test handling invalid channel IDs when setting parameters."""
        if expected_error:
            with pytest.raises(expected_error):
                qcm_rf.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
        else:
            qcm_rf.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
            sequencer = qcm_rf.get_sequencer(channel_id)
            assert sequencer.gain_i == 2.0
            assert sequencer.gain_q == 2.0

    def test_initial_setup(self, qcm_rf: QbloxQCMRF):
        """Test the initial setup of the QCM module."""
        qcm_rf.initial_setup()

        # Verify the correct setup calls were made on the device
        qcm_rf.device.disconnect_outputs.assert_called_once()
        for sequencer in qcm_rf.awg_sequencers:
            qcm_rf.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)

    def test_run(self, qcm_rf: QbloxQCMRF):
        """Test running the QCM module."""
        qcm_rf.sequences[0] = Sequence(
            program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights()
        )
        qcm_rf.run(channel_id=0)

        sequencer = qcm_rf.get_sequencer(0)
        qcm_rf.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        qcm_rf.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_upload_qpysequence(self, qcm_rf: QbloxQCMRF):
        """Test uploading a QpySequence to the QCM module."""
        sequence = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        qcm_rf.upload_qpysequence(qpysequence=sequence, channel_id=0)

        qcm_rf.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())

    def test_clear_cache(self, qcm_rf: QbloxQCMRF):
        """Test clearing the cache of the QCM module."""
        qcm_rf.cache = {0: MagicMock()}  # type: ignore[misc]
        qcm_rf.clear_cache()

        assert qcm_rf.cache == {}
        assert qcm_rf.sequences == {}

    def test_reset(self, qcm_rf: QbloxQCMRF):
        """Test resetting the QCM module."""
        qcm_rf.reset()

        qcm_rf.device.reset.assert_called_once()
        assert qcm_rf.cache == {}
        assert qcm_rf.sequences == {}

    def test_calibrate_mixers(self, qcm_rf: QbloxQCMRF):
        """Test calibrating the QCM mixers."""
        channel_id = 0
        cal_type = "lo"

        qcm_rf.calibrate_mixers(cal_type=cal_type, channel_id=channel_id)
        qcm_rf.device._run_mixer_lo_calib.assert_called_with(channel_id)

        cal_type = "lo_and_sidebands"

        qcm_rf.calibrate_mixers(cal_type=cal_type, channel_id=channel_id)
        qcm_rf.device._run_mixer_lo_calib.assert_called_with(channel_id)

        for sequencer in qcm_rf.device.sequencers:
            qcm_rf.device.sequencers[sequencer].sideband_cal.assert_called()

        cal_type = "oh hi Mark!"

        with pytest.raises(Exception):
            qcm_rf.calibrate_mixers(cal_type=cal_type, channel_id=channel_id)
