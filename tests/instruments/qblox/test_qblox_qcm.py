"""Tests for the Qblox Module class."""

import copy
import re
from unittest.mock import MagicMock, patch, create_autospec

import numpy as np
import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.instrument_controllers.qblox.qblox_cluster_controller import QbloxClusterController
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxQCM
from qililab.platform import Platform
from qililab.data_management import build_platform
from qililab.typings import Parameter
from typing import cast
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard="tests/instruments/qblox/qblox_runcard.yaml")


@pytest.fixture(name="qcm")
def fixture_qrm(platform: Platform):
    qcm = cast(QbloxQCM, platform.get_element(alias="qcm"))

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
        "offset_awg_path1"
    ]

    module_mock_spec = [
        *QcmQrm._get_required_parent_attr_names(),
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


class TestQbloxQCM:
    def test_init(self, qcm: QbloxQCM):
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

            # Test OFFSET_OUT settings
            (Parameter.OFFSET_OUT0, 0.1),
            (Parameter.OFFSET_OUT1, 0.15),
            (Parameter.OFFSET_OUT2, 0.2),
            (Parameter.OFFSET_OUT3, 0.25),
        ]
    )
    def test_set_parameter(self, qcm: QbloxQCM, parameter, value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        qcm.set_parameter(parameter, value, channel_id=0)
        sequencer = qcm.get_sequencer(0)

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
        elif parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            assert qcm.out_offsets[output] == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            # Invalid parameter (should raise ParameterNotFound)
            (Parameter.BUS_FREQUENCY, 42),  # Invalid parameter
        ]
    )
    def test_set_parameter_raises_error(self, qcm: QbloxQCM, parameter, value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        with pytest.raises(ParameterNotFound):
            qcm.set_parameter(parameter, value, channel_id=0)

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

            # Test OFFSET_OUT settings
            (Parameter.OFFSET_OUT0, 0.0),
            (Parameter.OFFSET_OUT1, 0.1),
            (Parameter.OFFSET_OUT2, 0.2),
            (Parameter.OFFSET_OUT3, 0.3),
        ]
    )
    def test_get_parameter(self, qcm: QbloxQCM, parameter, expected_value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        value = qcm.get_parameter(parameter, channel_id=0)
        assert value == expected_value

    def test_get_parameter_raises_error(self, qcm: QbloxQCM):
        """Test setting parameters for QCM sequencers using parameterized values."""
        with pytest.raises(ParameterNotFound):
            qcm.get_parameter(Parameter.BUS_FREQUENCY, channel_id=0)

    @pytest.mark.parametrize(
        "channel_id, expected_error",
        [
            (0, None),  # Valid channel ID
            (5, Exception),  # Invalid channel ID
        ]
    )
    def test_invalid_channel(self, qcm: QbloxQCM, channel_id, expected_error):
        """Test handling invalid channel IDs when setting parameters."""
        if expected_error:
            with pytest.raises(expected_error):
                qcm.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
        else:
            qcm.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
            sequencer = qcm.get_sequencer(channel_id)
            assert sequencer.gain_i == 2.0
            assert sequencer.gain_q == 2.0

    def test_initial_setup(self, qcm: QbloxQCM):
        """Test the initial setup of the QCM module."""
        qcm.initial_setup()

        # Verify the correct setup calls were made on the device
        qcm.device.disconnect_outputs.assert_called_once()
        for sequencer in qcm.awg_sequencers:
            qcm.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)

    def test_run(self, qcm: QbloxQCM):
        """Test running the QCM module."""
        qcm.sequences[0] = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        qcm.run(channel_id=0)

        sequencer = qcm.get_sequencer(0)
        qcm.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        qcm.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_upload_qpysequence(self, qcm: QbloxQCM):
        """Test uploading a QpySequence to the QCM module."""
        sequence = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        qcm.upload_qpysequence(qpysequence=sequence, channel_id=0)

        qcm.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())

    def test_clear_cache(self, qcm: QbloxQCM):
        """Test clearing the cache of the QCM module."""
        qcm.cache = {0: MagicMock()}
        qcm.clear_cache()

        assert qcm.cache == {}
        assert qcm.sequences == {}

    def test_reset(self, qcm: QbloxQCM):
        """Test resetting the QCM module."""
        qcm.reset()

        qcm.device.reset.assert_called_once()
        assert qcm.cache == {}
        assert qcm.sequences == {}
