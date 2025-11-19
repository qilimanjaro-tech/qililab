"""Tests for the Qblox Module class."""

from typing import cast
from unittest.mock import MagicMock

import pytest
from qblox_instruments.qcodes_drivers.module import Module as QcmQrm
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.data_management import build_platform
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxQRM
from qililab.platform import Platform
from qililab.qprogram.qblox_compiler import AcquisitionData
from qililab.typings import AcquireTriggerMode, IntegrationMode, Parameter


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard="tests/instruments/qblox/qblox_runcard.yaml")


@pytest.fixture(name="qrm")
def fixture_qrm(platform: Platform) -> QbloxQRM:
    qrm = cast(QbloxQRM, platform.get_element(alias="qrm"))

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
        "connect_acq_I",
        "connect_acq_Q",
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
    ]

    # Create a mock device using create_autospec to follow the interface of the expected device
    qrm.device = MagicMock()
    qrm.device.mock_add_spec(module_mock_spec)

    qrm.device.sequencers = {
        0: MagicMock(),
        1: MagicMock(),
    }

    for sequencer in qrm.device.sequencers:
        qrm.device.sequencers[sequencer].mock_add_spec(sequencer_mock_spec)

    return qrm


class TestQbloxQRM:
    def test_init(self, qrm: QbloxQRM):
        assert qrm.is_awg()
        assert qrm.is_adc()
        assert qrm.alias == "qrm"
        assert len(qrm.awg_sequencers) == 2  # As per the YAML config
        assert qrm.out_offsets == [0.0, 0.1, 0.2, 0.3]
        sequencer = qrm.get_sequencer(0)
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

    def test_init_raises_error(self):
        with pytest.raises(ValueError):
            _ = build_platform(runcard="tests/instruments/qblox/qblox_qrm_too_many_sequencers_runcard.yaml")

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
            (Parameter.SCOPE_ACQUIRE_TRIGGER_MODE, "sequencer"),
            (Parameter.SCOPE_ACQUIRE_TRIGGER_MODE, "level"),
            (Parameter.SCOPE_HARDWARE_AVERAGING, True),
            (Parameter.SCOPE_HARDWARE_AVERAGING, False),
            (Parameter.SAMPLING_RATE, 0.09),
            (Parameter.HARDWARE_DEMODULATION, True),
            (Parameter.HARDWARE_DEMODULATION, False),
            (Parameter.INTEGRATION_LENGTH, 100),
            (Parameter.INTEGRATION_MODE, "ssb"),
            (Parameter.SEQUENCE_TIMEOUT, 2),
            (Parameter.ACQUISITION_TIMEOUT, 2),
            (Parameter.TIME_OF_FLIGHT, 80),
            (Parameter.SCOPE_STORE_ENABLED, True),
            (Parameter.THRESHOLD, 0.5),
            (Parameter.THRESHOLD_ROTATION, 0.5),
        ],
    )
    def test_set_parameter(self, qrm: QbloxQRM, parameter, value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        qrm.set_parameter(parameter, value, channel_id=0)
        sequencer = qrm.get_sequencer(0)

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
        elif parameter == Parameter.SCOPE_ACQUIRE_TRIGGER_MODE:
            assert sequencer.scope_acquire_trigger_mode == AcquireTriggerMode(value)  # type: ignore[attr-defined]
        elif parameter == Parameter.INTEGRATION_LENGTH:
            assert sequencer.integration_length == value  # type: ignore[attr-defined]
        elif parameter == Parameter.SAMPLING_RATE:
            assert sequencer.sampling_rate == value  # type: ignore[attr-defined]
        elif parameter == Parameter.INTEGRATION_MODE:
            assert sequencer.integration_mode == IntegrationMode(value)  # type: ignore[attr-defined]
        elif parameter == Parameter.SEQUENCE_TIMEOUT:
            assert sequencer.sequence_timeout == value  # type: ignore[attr-defined]
        elif parameter == Parameter.ACQUISITION_TIMEOUT:
            assert sequencer.acquisition_timeout == value  # type: ignore[attr-defined]
        elif parameter == Parameter.TIME_OF_FLIGHT:
            assert sequencer.time_of_flight == value  # type: ignore[attr-defined]
        elif parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            assert qrm.out_offsets[output] == value

    def test_set_parameter_scope_store_enabled(self, qrm: QbloxQRM):
        """Test setting parameters for SCOPE_STORE_ENABLED that require the same instance of QRM."""
        sequencer = qrm.get_sequencer(0)

        qrm.set_parameter(Parameter.SCOPE_STORE_ENABLED, True, channel_id=0)
        assert sequencer.scope_store_enabled == bool(True)
        qrm._scoping_sequencer = 0
        qrm.set_parameter(Parameter.SCOPE_STORE_ENABLED, True, channel_id=0)
        assert sequencer.scope_store_enabled == bool(True)
        qrm.awg_sequencers[0].scope_store_enabled = False
        qrm._scoping_sequencer = 0
        qrm.set_parameter(Parameter.SCOPE_STORE_ENABLED, False, channel_id=0)
        assert sequencer.scope_store_enabled == bool(False)

    def test_set_parameter_raises_error(self, qrm: QbloxQRM):
        """Test setting parameters for QCM sequencers using parameterized values."""
        with pytest.raises(ParameterNotFound):
            qrm.set_parameter(Parameter.BUS_FREQUENCY, value=42, channel_id=0)

        with pytest.raises(IndexError):
            qrm.set_parameter(Parameter.PHASE_IMBALANCE, value=0.5, channel_id=4)

        with pytest.raises(Exception):
            qrm.set_parameter(Parameter.PHASE_IMBALANCE, value=0.5, channel_id=None)

        with pytest.raises(ValueError):
            qrm.awg_sequencers[0].scope_store_enabled = True
            qrm.awg_sequencers[0].identifier = 0
            qrm._scoping_sequencer = 1
            qrm.set_parameter(Parameter.SCOPE_STORE_ENABLED, value=True, channel_id=1)

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
            (Parameter.SCOPE_ACQUIRE_TRIGGER_MODE, "sequencer"),
            (Parameter.SCOPE_HARDWARE_AVERAGING, True),
            (Parameter.SAMPLING_RATE, 1.0e9),
            (Parameter.HARDWARE_DEMODULATION, True),
            (Parameter.INTEGRATION_LENGTH, 1000),
            (Parameter.INTEGRATION_MODE, "ssb"),
            (Parameter.SEQUENCE_TIMEOUT, 5.0),
            (Parameter.ACQUISITION_TIMEOUT, 1.0),
            (Parameter.TIME_OF_FLIGHT, 120),
            (Parameter.SCOPE_STORE_ENABLED, False),
            (Parameter.THRESHOLD, 1.0),
            (Parameter.THRESHOLD_ROTATION, 0.0),
        ],
    )
    def test_get_parameter(self, qrm: QbloxQRM, parameter, expected_value):
        """Test setting parameters for QCM sequencers using parameterized values."""
        value = qrm.get_parameter(parameter, channel_id=0)
        assert value == expected_value

    def test_get_parameter_raises_error(self, qrm: QbloxQRM):
        """Test setting parameters for QCM sequencers using parameterized values."""
        with pytest.raises(ParameterNotFound):
            qrm.get_parameter(Parameter.BUS_FREQUENCY, channel_id=0)

        with pytest.raises(IndexError):
            qrm.get_parameter(Parameter.PHASE_IMBALANCE, channel_id=4)

        with pytest.raises(Exception):
            qrm.get_parameter(Parameter.PHASE_IMBALANCE, channel_id=None)

    @pytest.mark.parametrize(
        "channel_id, expected_error",
        [
            (0, None),  # Valid channel ID
            (5, Exception),  # Invalid channel ID
        ],
    )
    def test_invalid_channel(self, qrm: QbloxQRM, channel_id, expected_error):
        """Test handling invalid channel IDs when setting parameters."""
        if expected_error:
            with pytest.raises(expected_error):
                qrm.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
        else:
            qrm.set_parameter(Parameter.GAIN, 2.0, channel_id=channel_id)
            sequencer = qrm.get_sequencer(channel_id)
            assert sequencer.gain_i == 2.0
            assert sequencer.gain_q == 2.0

    def test_initial_setup(self, qrm: QbloxQRM):
        """Test the initial setup of the QCM module."""
        qrm.initial_setup()

        # Verify the correct setup calls were made on the device
        qrm.device.disconnect_outputs.assert_called_once()
        for sequencer in qrm.awg_sequencers:
            qrm.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)

    def test_run(self, qrm: QbloxQRM):
        """Test running the QCM module."""
        qrm.sequences[0] = Sequence(
            program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights()
        )
        qrm.run(channel_id=0)

        sequencer = qrm.get_sequencer(0)
        qrm.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        qrm.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_upload_qpysequence(self, qrm: QbloxQRM):
        """Test uploading a QpySequence to the QCM module."""
        sequence = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        qrm.upload_qpysequence(qpysequence=sequence, channel_id=0)

        qrm.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())

    def test_acquire_qprogram_results(self, qrm: QbloxQRM):
        """Test uploading a QpySequence to the QCM module."""
        acquisitions = Acquisitions()
        acquisitions.add(name="acquisition_0")
        acquisitions.add(name="acquisition_1")

        sequence = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=acquisitions, weights=Weights())
        qrm.upload_qpysequence(qpysequence=sequence, channel_id=0)

        qp_acqusitions = {
            "acquisition_0": AcquisitionData(bus="readout_q0", save_adc=False, shape=(-1,), intertwined=1),
            "acquisition_1": AcquisitionData(bus="readout_q0", save_adc=True, shape=(-1,), intertwined=1),
        }

        qrm.acquire_qprogram_results(acquisitions=qp_acqusitions, channel_id=0)

        assert qrm.device.get_acquisition_status.call_count == 2
        assert qrm.device.store_scope_acquisition.call_count == 1
        assert qrm.device.get_acquisitions.call_count == 2
        assert qrm.device.delete_acquisition_data.call_count == 2

    def test_clear_cache(self, qrm: QbloxQRM):
        """Test clearing the cache of the QCM module."""
        qrm.cache = {0: MagicMock()}  # type: ignore[misc]
        qrm.clear_cache()

        assert qrm.cache == {}
        assert qrm.sequences == {}

    def test_reset(self, qrm: QbloxQRM):
        """Test resetting the QCM module."""
        qrm.reset()

        qrm.device.reset.assert_called_once()
        assert qrm.cache == {}
        assert qrm.sequences == {}
