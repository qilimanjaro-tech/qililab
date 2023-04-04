"""Tests for the QbloxQCM class."""
import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments import QbloxQCM
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter


class TestQbloxQCM:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_inital_setup_method(self, qcm: QbloxQCM):
        """Test initial_setup method"""
        qcm.initial_setup()
        qcm.device.out0_offset.assert_called()
        qcm.device.out1_offset.assert_called()
        qcm.device.out2_offset.assert_called()
        qcm.device.out3_offset.assert_called()
        qcm.device.sequencer0.sync_en.assert_called_with(qcm.awg_sequencers[0].sync_enabled)
        qcm.device.sequencer0.mod_en_awg.assert_called()
        qcm.device.sequencer0.offset_awg_path0.assert_called()
        qcm.device.sequencer0.offset_awg_path1.assert_called()
        qcm.device.sequencer0.mixer_corr_gain_ratio.assert_called()
        qcm.device.sequencer0.mixer_corr_phase_offset_degree.assert_called()

    def test_start_sequencer_method(self, qcm: QbloxQCM):
        """Test start_sequencer method"""
        qcm.start_sequencer()
        qcm.device.arm_sequencer.assert_called()
        qcm.device.start_sequencer.assert_called()

    @pytest.mark.parametrize(
        "parameter, value, channel_id",
        [
            (Parameter.GAIN, 0.02, 0),
            (Parameter.GAIN_PATH0, 0.03, 0),
            (Parameter.GAIN_PATH1, 0.01, 0),
            (Parameter.OFFSET_I, 0.9, 0),
            (Parameter.OFFSET_Q, 0.12, 0),
            (Parameter.OFFSET_OUT0, 1.234, None),
            (Parameter.OFFSET_OUT1, 0, None),
            (Parameter.OFFSET_OUT2, 0.123, None),
            (Parameter.OFFSET_OUT3, 10, None),
            (Parameter.OFFSET_PATH0, 0.8, 0),
            (Parameter.OFFSET_PATH1, 0.11, 0),
            (Parameter.IF, 100_000, 0),
            (Parameter.HARDWARE_MODULATION, True, 0),
            (Parameter.HARDWARE_MODULATION, False, 0),
            (Parameter.SYNC_ENABLED, False, 0),
            (Parameter.SYNC_ENABLED, True, 0),
            (Parameter.NUM_BINS, 1, 0),
            (Parameter.GAIN_IMBALANCE, 0.1, 0),
            (Parameter.PHASE_IMBALANCE, 0.09, 0),
        ],
    )
    def test_setup_method(self, parameter: Parameter, value: float | bool | int, channel_id: int, qcm: QbloxQCM):
        """Test setup method"""
        qcm.setup(parameter=parameter, value=value, channel_id=channel_id)
        if parameter == Parameter.GAIN:
            assert qcm.awg_sequencers[channel_id].gain_path0 == value
            assert qcm.awg_sequencers[channel_id].gain_path1 == value
        if parameter == Parameter.GAIN_PATH0:
            assert qcm.awg_sequencers[channel_id].gain_path0 == value
        if parameter == Parameter.GAIN_PATH1:
            assert qcm.awg_sequencers[channel_id].gain_path1 == value
        if parameter == Parameter.OFFSET_I:
            assert qcm.offset_i(sequencer_id=channel_id) == value
        if parameter == Parameter.OFFSET_Q:
            assert qcm.offset_q(sequencer_id=channel_id) == value
        if parameter == Parameter.OFFSET_PATH0:
            assert qcm.awg_sequencers[channel_id].offset_path0 == value
        if parameter == Parameter.OFFSET_PATH1:
            assert qcm.awg_sequencers[channel_id].offset_path1 == value
        if parameter == Parameter.IF:
            assert qcm.awg_sequencers[channel_id].intermediate_frequency == value
        if parameter == Parameter.HARDWARE_MODULATION:
            assert qcm.awg_sequencers[channel_id].hardware_modulation == value
        if parameter == Parameter.SYNC_ENABLED:
            assert qcm.awg_sequencers[channel_id].sync_enabled == value
        if parameter == Parameter.NUM_BINS:
            assert qcm.awg_sequencers[channel_id].num_bins == value
        if parameter == Parameter.GAIN_IMBALANCE:
            assert qcm.awg_sequencers[channel_id].gain_imbalance == value
        if parameter == Parameter.PHASE_IMBALANCE:
            assert qcm.awg_sequencers[channel_id].phase_imbalance == value
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            assert qcm.out_offsets[output] == value

    def test_setup_out_offset_raises_error(self, qcm: QbloxQCM):
        """Test that calling ``_set_out_offset`` with a wrong output value raises an error."""
        with pytest.raises(IndexError, match="Output 5 is out of range"):
            qcm._set_out_offset(output=5, value=1)

    def test_turn_off_method(self, qcm: QbloxQCM):
        """Test turn_off method"""
        qcm.turn_off()
        qcm.device.stop_sequencer.assert_called_once()

    def test_reset_method(self, qrm: QbloxQCM):
        """Test reset method"""
        qrm._cache = [None, 0, 0]  # type: ignore # pylint: disable=protected-access
        qrm.reset()
        assert qrm._cache is None  # pylint: disable=protected-access

    def test_upload_method(self, qcm: QbloxQCM):
        """Test upload method"""
        qcm.upload(
            sequences=[Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights={})]
        )
        qcm.device.sequencer0.sequence.assert_called_once()

    def test_id_property(self, qcm_no_device: QbloxQCM):
        """Test id property."""
        assert qcm_no_device.id_ == qcm_no_device.settings.id_

    def test_name_property(self, qcm_no_device: QbloxQCM):
        """Test name property."""
        assert qcm_no_device.name == InstrumentName.QBLOX_QCM

    def test_category_property(self, qcm_no_device: QbloxQCM):
        """Test category property."""
        assert qcm_no_device.category == qcm_no_device.settings.category

    def test_firmware_property(self, qcm_no_device: QbloxQCM):
        """Test firmware property."""
        assert qcm_no_device.firmware == qcm_no_device.settings.firmware

    def test_frequency_property(self, qcm_no_device: QbloxQCM):
        """Test frequency property."""
        assert qcm_no_device.frequency(0) == qcm_no_device.awg_sequencers[0].intermediate_frequency
