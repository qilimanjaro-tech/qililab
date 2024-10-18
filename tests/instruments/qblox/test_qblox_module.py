"""Tests for the Qblox Module class."""

import copy
import re
from unittest.mock import MagicMock, patch, create_autospec

import numpy as np
import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.instrument_controllers.qblox.qblox_cluster_controller import QbloxClusterController
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxModule, QbloxQCM, QbloxQRM
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseSchedule
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.qblox_compiler import QbloxCompiler
from qililab.typings.enums import Parameter
from qililab.typings.instruments.qcm_qrm import QcmQrm
from tests.data import Galadriel
from qililab.data_management import build_platform
from typing import cast


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard="tests/instruments/qblox/qblox_runcard.yaml")


@pytest.fixture(name="qcm")
def fixture_qrm(platform: Platform):
    qcm = cast(QbloxModule, platform.get_element(alias="qcm"))

    # Create a mock device using create_autospec to follow the interface of the expected device
    qcm.device = create_autospec(QcmQrm, instance=True)

    # Dynamically add `disconnect_outputs` and `sequencers` to the mock device
    qcm.device.disconnect_outputs = MagicMock()
    qcm.device.sequencers = {
        0: MagicMock(),  # Mock sequencer for identifier 0
        1: MagicMock(),  # Mock sequencer for identifier 1
    }
    qcm.device.out0_offset = MagicMock()

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
        qcm.run(channel_id=0)

        sequencer = qcm.get_sequencer(0)
        qcm.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        qcm.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_upload_qpysequence(self, qcm: QbloxModule):
        """Test uploading a QpySequence to the QCM module."""
        mock_sequence = create_autospec(Sequence, instance=True)
        qcm.upload_qpysequence(qpysequence=mock_sequence, channel_id=0)

        sequencer = qcm.get_sequencer(0)
        qcm.device.sequencers[sequencer.identifier].sequence.assert_called_once_with(mock_sequence)

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
