"""Tests for the Qblox Module class."""

from typing import cast
from unittest.mock import MagicMock

import pytest
from qblox_instruments.qcodes_drivers.module import Module as QcmQrm
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.data_management import build_platform
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxQRMRF
from qililab.platform import Platform
from qililab.typings import Parameter

MAX_ATTENUATION = 30


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard="tests/instruments/qblox/qblox_runcard.yaml")


@pytest.fixture(name="qrm_rf")
def fixture_qrm(platform: Platform):
    qrm_rf = cast(QbloxQRMRF, platform.get_element(alias="qrm-rf"))

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
        "connect_acq",
        "thresholded_acq_threshold",
        "thresholded_acq_rotation",
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
        "out0_in0_lo_freq_cal_type_default",
    ]

    # Create a mock device using create_autospec to follow the interface of the expected device
    qrm_rf.device = MagicMock()
    qrm_rf.device.mock_add_spec(module_mock_spec)
    qrm_rf.device._get_max_out_att_0 = MagicMock(return_value=MAX_ATTENUATION)
    qrm_rf.device._run_mixer_lo_calib = MagicMock()

    qrm_rf.device.sequencers = {0: MagicMock(), 1: MagicMock()}

    for sequencer in qrm_rf.device.sequencers:
        qrm_rf.device.sequencers[sequencer].mock_add_spec(sequencer_mock_spec)
        qrm_rf.device.sequencers[sequencer].sideband_cal = MagicMock()

    return qrm_rf


class TestQbloxQRMRF:
    def test_init(self, qrm_rf: QbloxQRMRF):
        assert qrm_rf.alias == "qrm-rf"
        assert len(qrm_rf.awg_sequencers) == 2

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
            # QRM-RF specific
            (Parameter.LO_FREQUENCY, 5e9),
            (Parameter.OUT0_IN0_LO_FREQ, 5e9),
            (Parameter.OUT0_IN0_LO_EN, True),
            (Parameter.OUT0_ATT, 5),
            (Parameter.IN0_ATT, 5),
            (Parameter.OUT0_OFFSET_PATH0, 0.5),
            (Parameter.OUT0_OFFSET_PATH1, 6e9),
        ],
    )
    def test_set_parameter(self, qrm_rf: QbloxQRMRF, parameter, value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        qrm_rf.set_parameter(parameter, value, channel_id=0)
        sequencer = qrm_rf.get_sequencer(0)

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
        elif parameter == Parameter.OUT0_IN0_LO_FREQ:
            assert qrm_rf.settings.out0_in0_lo_freq == value
        elif parameter == Parameter.OUT0_IN0_LO_EN:
            assert qrm_rf.settings.out0_in0_lo_en == value
        elif parameter == Parameter.OUT0_ATT:
            assert qrm_rf.settings.out0_att == value
        elif parameter == Parameter.IN0_ATT:
            assert qrm_rf.settings.in0_att == value
        elif parameter == Parameter.OUT0_OFFSET_PATH0:
            assert qrm_rf.settings.out0_offset_path0 == value
        elif parameter == Parameter.OUT0_OFFSET_PATH0:
            assert qrm_rf.settings.out0_offset_path1 == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            # Invalid parameter (should raise ParameterNotFound)
            (Parameter.BUS_FREQUENCY, 42),  # Invalid parameter
        ],
    )
    def test_set_parameter_raises_error(self, qrm_rf: QbloxQRMRF, parameter, value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        with pytest.raises(ParameterNotFound):
            qrm_rf.set_parameter(parameter, value, channel_id=0)

        with pytest.raises(Exception):
            qrm_rf.set_parameter(Parameter.OUT0_ATT, value=MAX_ATTENUATION + 10, channel_id=None)

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
            # QRM-RF specific
            (Parameter.LO_FREQUENCY, 3e9),
            (Parameter.OUT0_IN0_LO_FREQ, 3e9),
            (Parameter.OUT0_IN0_LO_EN, True),
            (Parameter.OUT0_ATT, 10),
            (Parameter.IN0_ATT, 2),
            (Parameter.OUT0_OFFSET_PATH0, 0.2),
            (Parameter.OUT0_OFFSET_PATH1, 0.07),
        ],
    )
    def test_get_parameter(self, qrm_rf: QbloxQRMRF, parameter, expected_value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        value = qrm_rf.get_parameter(parameter, channel_id=0)
        assert value == expected_value

    def test_get_parameter_raises_error(self, qrm_rf: QbloxQRMRF):
        """Test setting parameters for QCM sequencers using parameterized values."""
        with pytest.raises(ParameterNotFound):
            qrm_rf.get_parameter(Parameter.BUS_FREQUENCY, channel_id=0)

    @pytest.mark.parametrize(
        "channel_id, expected_error",
        [
            (0, None),  # Valid channel ID
            (5, Exception),  # Invalid channel ID
        ],
    )
    def test_invalid_channel(self, qrm_rf: QbloxQRMRF, channel_id, expected_error):
        """Test handling invalid channel IDs when setting parameters."""
        if expected_error:
            with pytest.raises(expected_error):
                qrm_rf.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
        else:
            qrm_rf.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
            sequencer = qrm_rf.get_sequencer(channel_id)
            assert sequencer.gain_i == 2.0
            assert sequencer.gain_q == 2.0

    def test_initial_setup(self, qrm_rf: QbloxQRMRF):
        """Test the initial setup of the QCM module."""
        qrm_rf.initial_setup()

        # Verify the correct setup calls were made on the device
        qrm_rf.device.disconnect_outputs.assert_called_once()
        qrm_rf.device.disconnect_inputs.assert_called_once()
        for sequencer in qrm_rf.awg_sequencers:
            qrm_rf.device.sequencers[sequencer.identifier].connect_out0.assert_called_with("IQ")
            qrm_rf.device.sequencers[sequencer.identifier].connect_acq.assert_called_with("in0")
            qrm_rf.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)

    def test_run(self, qrm_rf: QbloxQRMRF):
        """Test running the QCM module."""
        qrm_rf.sequences[0] = Sequence(
            program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights()
        )
        qrm_rf.run(channel_id=0)

        sequencer = qrm_rf.get_sequencer(0)
        qrm_rf.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        qrm_rf.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_upload_qpysequence(self, qrm_rf: QbloxQRMRF):
        """Test uploading a QpySequence to the QCM module."""
        sequence = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        qrm_rf.upload_qpysequence(qpysequence=sequence, channel_id=0)

        qrm_rf.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())

    def test_clear_cache(self, qrm_rf: QbloxQRMRF):
        """Test clearing the cache of the QCM module."""
        qrm_rf.cache = {0: MagicMock()}  # type: ignore[misc]
        qrm_rf.clear_cache()

        assert qrm_rf.cache == {}
        assert qrm_rf.sequences == {}

    def test_reset(self, qrm_rf: QbloxQRMRF):
        """Test resetting the QCM module."""
        qrm_rf.reset()

        qrm_rf.device.reset.assert_called_once()
        assert qrm_rf.cache == {}
        assert qrm_rf.sequences == {}

    def test_calibrate_mixers(self, qrm_rf: QbloxQRMRF):
        """Test calibrating the QRM mixers."""
        channel_id = 0
        cal_type = "lo"

        qrm_rf.calibrate_mixers(cal_type=cal_type, channel_id=channel_id)
        qrm_rf.device._run_mixer_lo_calib.assert_called_with(channel_id)

        cal_type = "lo_and_sidebands"

        qrm_rf.calibrate_mixers(cal_type=cal_type, channel_id=channel_id)
        qrm_rf.device._run_mixer_lo_calib.assert_called_with(channel_id)

        for sequencer in qrm_rf.device.sequencers:
            qrm_rf.device.sequencers[sequencer].sideband_cal.assert_called()

        cal_type = "oh hi Mark!"

        with pytest.raises(Exception):
            qrm_rf.calibrate_mixers(cal_type=cal_type, channel_id=channel_id)
