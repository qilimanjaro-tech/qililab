"""Tests for the Qblox Module class."""

import copy
import re
from unittest.mock import MagicMock, patch, create_autospec

import numpy as np
import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.instrument_controllers.qblox.qblox_cluster_controller import QbloxClusterController
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxModule
from qililab.platform import Platform
from qililab.data_management import build_platform
from typing import cast


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard="tests/instruments/qblox/qblox_runcard.yaml")


@pytest.fixture(name="qcm")
def fixture_qrm(platform: Platform):
    qcm = cast(QbloxModule, platform.get_element(alias="qcm"))

    sequencer_mock_spec = [
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
        "offset_awg_path1"
    ]

    module_mock_spec = [
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
        "reset"
    ]

    # Create a mock device using create_autospec to follow the interface of the expected device
    qcm.device = MagicMock()
    qcm.device.mock_add_spec(module_mock_spec)

    qcm.device.sequencers = {
        0: MagicMock(),
        1: MagicMock(),
    }

    for sequencer in qcm.device.sequencers:
        qcm.device.sequencers[sequencer].mock_add_spec(sequencer_mock_spec)

    return qcm


class TestQbloxModule:
    def test_init(self, qcm: QbloxModule):
        assert qcm.alias == "qcm"
        assert len(qcm.awg_sequencers) == 2  # As per the YAML config
        assert qcm.out_offsets == [0.0, 0.1, 0.2, 0.3]
        sequencer = qcm.get_sequencer(0)
        assert sequencer.identifier == 0
        assert sequencer.outputs == [3, 2]
        assert sequencer.intermediate_frequency == 100e6
        assert sequencer.gain_imbalance == 0.05
        assert sequencer.phase_imbalance == 0.02
        assert sequencer.hardware_modulation is True
        assert sequencer.gain_i == 1.0
        assert sequencer.gain_q == 1.0
        assert sequencer.offset_i == 0.0
        assert sequencer.offset_q == 0.0
        assert sequencer.num_bins == 1024

    @pytest.mark.parametrize(
        "parameter, value, expected_gain_i, expected_gain_q, expected_error",
        [
            (Parameter.GAIN, 2.0, 2.0, 2.0, None),  # Valid case
            (Parameter.GAIN, 3.5, 3.5, 3.5, None),  # Another valid case
            (MagicMock(), 42, None, None, ParameterNotFound),  # Invalid parameter
        ]
    )
    def test_set_parameter(self, qcm: QbloxModule, parameter, value, expected_gain_i, expected_gain_q, expected_error):
        """Test setting parameters for QCM sequencers using parameterized values."""
        if expected_error:
            with pytest.raises(expected_error):
                qcm.set_parameter(parameter, value, channel_id=0)
        else:
            qcm.set_parameter(parameter, value, channel_id=0)
            sequencer = qcm.get_sequencer(0)
            assert sequencer.gain_i == expected_gain_i
            assert sequencer.gain_q == expected_gain_q

    @pytest.mark.parametrize(
        "channel_id, expected_error",
        [
            (0, None),  # Valid channel ID
            (5, Exception),  # Invalid channel ID
        ]
    )
    def test_invalid_channel(self, qcm: QbloxModule, channel_id, expected_error):
        """Test handling invalid channel IDs when setting parameters."""
        if expected_error:
            with pytest.raises(expected_error):
                qcm.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
        else:
            qcm.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
            sequencer = qcm.get_sequencer(channel_id)
            assert sequencer.gain_i == 2.0
            assert sequencer.gain_q == 2.0

    def test_initial_setup(self, qcm: QbloxModule):
        """Test the initial setup of the QCM module."""
        qcm.initial_setup()

        # Verify the correct setup calls were made on the device
        qcm.device.disconnect_outputs.assert_called_once()
        for idx in range(qcm.num_sequencers):
            sequencer = qcm.get_sequencer(idx)
            qcm.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)

    def test_run(self, qcm: QbloxModule):
        """Test running the QCM module."""
        qcm.sequences[0] = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        qcm.run(channel_id=0)

        sequencer = qcm.get_sequencer(0)
        qcm.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        qcm.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_upload_qpysequence(self, qcm: QbloxModule):
        """Test uploading a QpySequence to the QCM module."""
        sequence = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        qcm.upload_qpysequence(qpysequence=sequence, channel_id=0)

        qcm.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())

    def test_clear_cache(self, qcm: QbloxModule):
        """Test clearing the cache of the QCM module."""
        qcm.cache = {0: MagicMock()}
        qcm.clear_cache()

        assert qcm.cache == {}
        assert qcm.sequences == {}

    def test_reset(self, qcm: QbloxModule):
        """Test resetting the QCM module."""
        qcm.reset()

        qcm.device.reset.assert_called_once()
        assert qcm.cache == {}
        assert qcm.sequences == {}
