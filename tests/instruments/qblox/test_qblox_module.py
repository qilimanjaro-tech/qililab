"""Tests for the Qblox Module class."""

from typing import cast
from unittest.mock import MagicMock

import numpy as np
import pytest
from qblox_instruments.qcodes_drivers.module import Module as QcmQrm
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.data_management import build_platform
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.qblox import QbloxModule
from qililab.platform import Platform
from qililab.typings import DistortionState, Parameter
from qililab.utils import hash_qpy_sequence_components


def _build_sequence(waveform_data: list[float]) -> Sequence:
    """Build a QpySequence with the given waveform data and empty program/weights/acquisitions."""
    waveforms = Waveforms()
    waveforms.add(np.array(waveform_data, dtype=float))
    return Sequence(program=Program(), waveforms=waveforms, acquisitions=Acquisitions(), weights=Weights())

@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    InstrumentFactory.handlers["QBloxModule"] = QbloxModule
    return build_platform(runcard="tests/instruments/qblox/qblox_module_runcard.yml")


@pytest.fixture(name="module")
def fixture_module(platform: Platform) -> QbloxModule:
    module = cast(QbloxModule, platform.get_element(alias="module"))
    # ``QbloxModule`` is abstract: concrete QCM/QRM subclasses assign ``name``, the base does not.
    # It is only used to format the ParameterNotFound message, so a placeholder is enough here.
    module.name = "QBloxModule"  # type: ignore[assignment]

    sequencer_mock_spec = [
        *Sequencer._get_required_parent_attr_names(),
        "sync_en",
        "gain_awg_path0",
        "gain_awg_path1",
        "sequence",
        "update_sequence",
        "get_waveforms",
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
        "marker_ovr_value",
        "offset_awg_path0",
        "offset_awg_path1",
        "connect_acq_I",
        "connect_acq_Q",
        "thresholded_acq_threshold",
        "thresholded_acq_rotation",
        "thresholded_acq_trigger_address",
        "thresholded_acq_trigger_en"
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
        "module_type",
        "out0_exp0_amplitude",
        "out1_exp0_amplitude",
        "out2_exp0_amplitude",
        "out3_exp0_amplitude",
        "out0_exp1_amplitude",
        "out1_exp1_amplitude",
        "out2_exp1_amplitude",
        "out3_exp1_amplitude",
        "out0_exp2_amplitude",
        "out1_exp2_amplitude",
        "out2_exp2_amplitude",
        "out3_exp2_amplitude",
        "out0_exp0_time_constant",
        "out1_exp0_time_constant",
        "out2_exp0_time_constant",
        "out3_exp0_time_constant",
        "out0_exp2_time_constant",
        "out0_exp1_time_constant",
        "out0_fir_coeffs",
        "out1_fir_coeffs",
        "out2_fir_coeffs",
        "out3_fir_coeffs",
        "out0_fir_config",
        "out1_fir_config",
        "out2_fir_config",
        "out3_fir_config",
        "out0_exp0_config",
        "out1_exp0_config",
        "out2_exp0_config",
        "out3_exp0_config",
        "out0_exp1_config",
        "out1_exp1_config",
        "out2_exp1_config",
        "out3_exp1_config",
        "out0_exp2_config",
        "out1_exp2_config",
        "out2_exp2_config",
        "out3_exp2_config",
    ]
    

    # Create a mock device using create_autospec to follow the interface of the expected device
    module.device = MagicMock()
    module.device.mock_add_spec(module_mock_spec)

    module.device.sequencers = {
        0: MagicMock(),
        1: MagicMock(),
    }

    for sequencer in module.device.sequencers:
        module.device.sequencers[sequencer].mock_add_spec(sequencer_mock_spec)

    return module

class TestQbloxModule:
    def test_init(self, module: QbloxModule):
        """Test the base-class attributes parsed from the runcard."""
        assert module.alias == "module"
        assert module.num_sequencers == 2
        assert len(module.awg_sequencers) == 2  # As per the YAML config
        assert module.out_offsets == [0.0, 0.1, 0.2, 0.3]

        sequencer = module.get_sequencer(0)
        assert sequencer.identifier == 0
        assert sequencer.outputs == [3, 2]
        assert sequencer.intermediate_frequency == pytest.approx(100e6)
        assert sequencer.gain_imbalance == pytest.approx(0.05)
        assert sequencer.phase_imbalance == pytest.approx(0.02)
        assert sequencer.hardware_modulation is True
        assert sequencer.gain_i == pytest.approx(1.0)
        assert sequencer.gain_q == pytest.approx(1.0)
        assert sequencer.offset_i == pytest.approx(0.0)
        assert sequencer.offset_q == pytest.approx(0.0)

    def test_get_sequencer(self, module: QbloxModule):
        sequencer = module.get_sequencer(1)
        assert sequencer.identifier == 1

    def test_get_sequencer_raises_error(self, module: QbloxModule):
        with pytest.raises(IndexError, match="There is no sequencer with id=5."):
            module.get_sequencer(5)

    def test_get_filter(self, module: QbloxModule):
        test_filter = module.get_filter(0)
        assert test_filter.output_id == 0
        assert test_filter.exponential_amplitude[0] == pytest.approx(0.31)
        assert test_filter.exponential_time_constant[0] == 200
        assert test_filter.exponential_state == ["enabled", "enabled", "bypassed", None]
        assert test_filter.fir_coeff == [0.4] * 32
        assert test_filter.fir_state == "enabled"

    def test_get_filter_raises_error(self, module: QbloxModule):
        with pytest.raises(IndexError, match="There is no filter with id=3."):
            module.get_filter(3)

    def test_module_type(self, module: QbloxModule):
        _ = module.module_type()
        module.device.module_type.assert_called_once()

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
        ],
    )
    def test_set_parameter(self, module: QbloxModule, parameter, value):
        """Test setting sequencer/output parameters using parameterized values."""
        module.set_parameter(parameter, value, channel_id=0)
        sequencer = module.get_sequencer(0)

        if parameter == Parameter.GAIN:
            assert sequencer.gain_i == pytest.approx(value)
            assert sequencer.gain_q == pytest.approx(value)
        elif parameter == Parameter.GAIN_I:
            assert sequencer.gain_i == pytest.approx(value)
        elif parameter == Parameter.GAIN_Q:
            assert sequencer.gain_q == pytest.approx(value)
        elif parameter == Parameter.OFFSET_I:
            assert sequencer.offset_i == pytest.approx(value)
        elif parameter == Parameter.OFFSET_Q:
            assert sequencer.offset_q == pytest.approx(value)
        elif parameter == Parameter.IF:
            assert sequencer.intermediate_frequency == pytest.approx(value)
        elif parameter == Parameter.HARDWARE_MODULATION:
            assert sequencer.hardware_modulation == value
        elif parameter == Parameter.GAIN_IMBALANCE:
            assert sequencer.gain_imbalance == pytest.approx(value)
        elif parameter == Parameter.PHASE_IMBALANCE:
            assert sequencer.phase_imbalance == pytest.approx(value)
        elif parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            assert module.out_offsets[output] == pytest.approx(value)

    def test_set_parameter_gain(self, module: QbloxModule):
        """Test that setting GAIN updates both I and Q gains."""
        module.set_parameter(Parameter.GAIN, 2.0, channel_id=0)
        sequencer = module.get_sequencer(0)
        assert sequencer.gain_i == pytest.approx(2.0)
        assert sequencer.gain_q == pytest.approx(2.0)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.EXPONENTIAL_AMPLITUDE_1, 0.7),
            (Parameter.EXPONENTIAL_TIME_CONSTANT_2, 200),
            (Parameter.EXPONENTIAL_STATE_0, "enabled"),
            (Parameter.FIR_COEFF, [0.4] * 32),
            (Parameter.FIR_STATE, DistortionState.ENABLED),
        ],
    )
    def test_set_parameter_filters(self, module: QbloxModule, parameter, value):
        """Test setting filter parameters using parameterized values."""
        output_id = 0
        module.set_parameter(parameter=parameter, value=value, output_id=output_id)
        test_filter = module.get_filter(output_id)
        if parameter == Parameter.EXPONENTIAL_AMPLITUDE_1:
            assert test_filter.exponential_amplitude[1] == pytest.approx(value)
        elif parameter == Parameter.EXPONENTIAL_TIME_CONSTANT_2:
            assert test_filter.exponential_time_constant[2] == value
        elif parameter == Parameter.EXPONENTIAL_STATE_0:
            assert test_filter.exponential_state[0] == value
        elif parameter == Parameter.FIR_COEFF:
            assert test_filter.fir_coeff == value
        elif parameter == Parameter.FIR_STATE:
            assert test_filter.fir_state == value

    def test_set_parameter_raises_error(self, module: QbloxModule):
        """Test the error paths of set_parameter."""
        with pytest.raises(ParameterNotFound):
            module.set_parameter(Parameter.BUS_FREQUENCY, value=42, channel_id=0)

        with pytest.raises(IndexError):
            module.set_parameter(Parameter.PHASE_IMBALANCE, value=0.5, channel_id=4)

        with pytest.raises(Exception):
            module.set_parameter(Parameter.PHASE_IMBALANCE, value=0.5, channel_id=None)

    def test_set_filter_no_output_id(self, module: QbloxModule):
        "Tests that setting a filter parameter without specifying the output id raises an exception"
        parameter = Parameter.EXPONENTIAL_AMPLITUDE_0
        with pytest.raises(Exception, match=f"Cannot update parameter {parameter.value} without specifying an output_id."):
            module.set_parameter(parameter, value=0.5)

        parameter = Parameter.EXPONENTIAL_TIME_CONSTANT_0
        with pytest.raises(Exception, match=f"Cannot update parameter {parameter.value} without specifying an output_id."):
            module.set_parameter(parameter, value=15)

        parameter = Parameter.EXPONENTIAL_STATE_0
        with pytest.raises(Exception, match=f"Cannot update parameter {parameter.value} without specifying an output_id."):
            module.set_parameter(parameter, value=True)

        parameter = Parameter.FIR_STATE
        with pytest.raises(Exception, match=f"Cannot update parameter {parameter.value} without specifying an output_id."):
            module.set_parameter(parameter, value=True)

        parameter = Parameter.FIR_COEFF
        with pytest.raises(Exception, match=f"Cannot update parameter {parameter.value} without specifying an output_id."):
            module.set_parameter(parameter, value=None)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.EXPONENTIAL_STATE_0, True),
            (Parameter.FIR_STATE, True),
        ],
    )
    def test_state_converted_to_string_true(self, module: QbloxModule, parameter, value):
        """Test setting state parameters of filters as bool converts them to the string from DistortionState."""
        output_id = 0
        module.set_parameter(parameter=parameter, value=value, output_id=output_id)
        test_filter = module.get_filter(output_id)
        if parameter == Parameter.EXPONENTIAL_STATE_0:
            assert test_filter.exponential_state[0] == DistortionState.ENABLED
        elif parameter == Parameter.FIR_STATE:
            assert test_filter.fir_state == DistortionState.ENABLED

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.EXPONENTIAL_STATE_0, False),
            (Parameter.FIR_STATE, False),
        ],
    )
    def test_state_converted_to_string_false(self, module: QbloxModule, parameter, value):
        """Test setting state parameters of filters as bool converts them to the string from DistortionState."""
        output_id = 0
        module.set_parameter(parameter=parameter, value=value, output_id=output_id)
        test_filter = module.get_filter(output_id)
        if parameter == Parameter.EXPONENTIAL_STATE_0:
            assert test_filter.exponential_state[0] == DistortionState.BYPASSED
        elif parameter == Parameter.FIR_STATE:
            assert test_filter.fir_state == DistortionState.BYPASSED

    @pytest.mark.parametrize(
        "parameter, expected_value",
        [
            (Parameter.GAIN_I, 1.0),
            (Parameter.GAIN_Q, 1.0),
            (Parameter.OFFSET_I, 0.0),
            (Parameter.OFFSET_Q, 0.0),
            (Parameter.IF, 100e6),
            (Parameter.HARDWARE_MODULATION, True),
            (Parameter.GAIN_IMBALANCE, 0.05),
            (Parameter.PHASE_IMBALANCE, 0.02),
            (Parameter.OFFSET_OUT0, 0.0),
            (Parameter.OFFSET_OUT1, 0.1),
            (Parameter.OFFSET_OUT2, 0.2),
            (Parameter.OFFSET_OUT3, 0.3),
        ],
    )
    def test_get_parameter(self, module: QbloxModule, parameter, expected_value):
        """Test getting sequencer/output parameters using parameterized values."""
        value = module.get_parameter(parameter, channel_id=0)
        assert value == expected_value

    @pytest.mark.parametrize(
        "parameter, expected_value",
        [
            (Parameter.EXPONENTIAL_AMPLITUDE_2, 0.1),
            (Parameter.EXPONENTIAL_TIME_CONSTANT_2, 0.5),
            (Parameter.EXPONENTIAL_STATE_2, DistortionState.BYPASSED),
            (Parameter.FIR_COEFF, [0.4] * 32),
            (Parameter.FIR_STATE, DistortionState.ENABLED),
        ],
    )
    def test_get_parameter_filters(self, module: QbloxModule, parameter, expected_value):
        """Test getting filter parameters using parameterized values."""
        output_id = 0
        value = module.get_parameter(parameter, output_id=output_id)
        assert value == expected_value

    def test_get_parameter_raises_error(self, module: QbloxModule):
        """Test the error paths of get_parameter."""
        with pytest.raises(ParameterNotFound):
            module.get_parameter(Parameter.BUS_FREQUENCY, channel_id=0)

        with pytest.raises(IndexError):
            module.get_parameter(Parameter.PHASE_IMBALANCE, channel_id=4)

        with pytest.raises(IndexError):
            module.get_parameter(Parameter.EXPONENTIAL_STATE_2, output_id=2)

        with pytest.raises(Exception):
            module.get_parameter(Parameter.PHASE_IMBALANCE, channel_id=None)

    def test_get_filter_no_output_id(self, module: QbloxModule):
        "Tests that getting a filter parameter without specifying the output id raises an exception"
        parameter = Parameter.EXPONENTIAL_AMPLITUDE_0
        with pytest.raises(Exception, match=f"Cannot retrieve parameter {parameter.value} without specifying an output_id."):
            module.get_parameter(parameter)

        parameter = Parameter.EXPONENTIAL_TIME_CONSTANT_0
        with pytest.raises(Exception, match=f"Cannot retrieve parameter {parameter.value} without specifying an output_id."):
            module.get_parameter(parameter)

        parameter = Parameter.EXPONENTIAL_STATE_0
        with pytest.raises(Exception, match=f"Cannot retrieve parameter {parameter.value} without specifying an output_id."):
            module.get_parameter(parameter)

        parameter = Parameter.FIR_STATE
        with pytest.raises(Exception, match=f"Cannot retrieve parameter {parameter.value} without specifying an output_id."):
            module.get_parameter(parameter)

        parameter = Parameter.FIR_COEFF
        with pytest.raises(Exception, match=f"Cannot retrieve parameter {parameter.value} without specifying an output_id."):
            module.get_parameter(parameter)

    def test_initial_setup(self, module: QbloxModule):
        """Test the initial setup of the Qblox module."""
        module.initial_setup()

        # Verify the correct setup calls were made on the device
        module.device.disconnect_outputs.assert_called_once()
        for sequencer in module.awg_sequencers:
            module.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)

    def test_sync_sequencer(self, module: QbloxModule):
        module.sync_sequencer(sequencer_id=0)

        module.device.sequencers[0].sync_en.assert_called_once_with(True)

    def test_desync_sequencer(self, module: QbloxModule):
        module.desync_sequencer(sequencer_id=0)

        module.device.sequencers[0].sync_en.assert_called_once_with(False)

    def test_desync_sequencers(self, module: QbloxModule):
        module.desync_sequencers()

        for sequencer in module.awg_sequencers:
            module.device.sequencers[sequencer.identifier].sync_en.assert_called_once_with(False)

    def test_set_markers_override_enabled(self, module: QbloxModule):
        module.set_markers_override_enabled(value=True, sequencer_id=0)
        module.device.sequencers[0].marker_ovr_en.assert_called_with(True)

        module.set_markers_override_enabled(value=False, sequencer_id=0)
        module.device.sequencers[0].marker_ovr_en.assert_called_with(False)

    def test_set_markers_override_value(self, module: QbloxModule):
        module.set_markers_override_value(value=123, sequencer_id=0)
        module.device.sequencers[0].marker_ovr_value.assert_called_once_with(123)

    def test_clear_cache(self, module: QbloxModule):
        module.cache = {0: MagicMock()}  # type: ignore[misc]
        module.clear_cache()

        assert module.cache == {}
        assert module.sequences == {}
        assert module._qpy_sequence_hashes == {}

    def test_reset(self, module: QbloxModule):
        """Test resetting the Qblox module."""
        module.reset()

        module.device.reset.assert_called_once()
        assert module.cache == {}
        assert module.sequences == {}
        assert module._qpy_sequence_hashes == {}

    def test_turn_off(self, module: QbloxModule):
        module.turn_off()

        assert module.device.stop_sequencer.call_count == 2

    def test_turn_on(self, module: QbloxModule):
        """Test that turning on the module does not raise (no-op on the base class)."""
        module.turn_on()

    def test_run(self, module: QbloxModule):
        """Test running an uploaded program on the Qblox module."""
        module.sequences[0] = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        module.run(channel_id=0)

        sequencer = module.get_sequencer(0)
        module.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        module.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_upload(self, module: QbloxModule):
        """Test uploading a previously compiled sequence to the Qblox module."""
        module.sequences[0] = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        module.upload(channel_id=0)

        module.device.sequencers[0].sequence.assert_called_once_with(module.sequences[0].todict())
        module.device.sequencers[0].sync_en.assert_called_once_with(True)

    def test_upload_qpysequence_first_upload_is_full(self, module: QbloxModule):
        """First upload for a sequencer pushes the full sequence and seeds the cache."""
        sequence = _build_sequence([0.0, 0.1, 0.2])
        module.upload_qpysequence(qpysequence=sequence, channel_id=0)

        module.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())
        module.device.sequencers[0].update_sequence.assert_not_called()
        assert module.sequences[0] is sequence
        assert module._qpy_sequence_hashes[0] == hash_qpy_sequence_components(sequence)

    def test_upload_qpysequence_no_sequencer(self, module: QbloxModule):
        """Nothing is uploaded or cached when the channel has no associated sequencer."""
        module.upload_qpysequence(qpysequence=_build_sequence([0.0, 0.1, 0.2]), channel_id=5)

        module.device.sequencers[0].sequence.assert_not_called()
        module.device.sequencers[0].update_sequence.assert_not_called()
        assert module.sequences == {}
        assert module._qpy_sequence_hashes == {}

    def test_upload_qpysequence_unchanged_reupload_is_partial(self, module: QbloxModule):
        """Re-uploading an identical sequence updates only acquisitions via update_sequence."""
        sequence = _build_sequence([0.0, 0.1, 0.2])
        module.upload_qpysequence(qpysequence=sequence, channel_id=0)
        module.device.sequencers[0].sequence.reset_mock()

        module.upload_qpysequence(qpysequence=sequence, channel_id=0)

        module.device.sequencers[0].sequence.assert_not_called()
        module.device.sequencers[0].update_sequence.assert_called_once()
        call_kwargs = module.device.sequencers[0].update_sequence.call_args.kwargs
        assert set(call_kwargs) == {"acquisitions", "erase_existing"}
        assert call_kwargs["erase_existing"] is True

    def test_upload_qpysequence_changed_component_only(self, module: QbloxModule):
        """Changing only the waveforms re-uploads waveforms + acquisitions, not program/weights."""
        module.upload_qpysequence(qpysequence=_build_sequence([0.0, 0.1, 0.2]), channel_id=0)
        module.upload_qpysequence(qpysequence=_build_sequence([0.9, 0.8, 0.7]), channel_id=0)

        call_kwargs = module.device.sequencers[0].update_sequence.call_args.kwargs
        assert "waveforms" in call_kwargs
        assert "acquisitions" in call_kwargs
        assert "program" not in call_kwargs
        assert "weights" not in call_kwargs
        assert call_kwargs["erase_existing"] is True

    def test_upload_qpysequence_commits_only_after_successful_write(self, module: QbloxModule):
        """A failed device write leaves the cache unchanged, so the next run re-uploads instead of skipping."""
        module.upload_qpysequence(qpysequence=_build_sequence([0.0, 0.1, 0.2]), channel_id=0)
        hashes_after_first = dict(module._qpy_sequence_hashes[0])

        changed = _build_sequence([0.9, 0.8, 0.7])
        module.device.sequencers[0].update_sequence.side_effect = RuntimeError("device write failed")
        with pytest.raises(RuntimeError):
            module.upload_qpysequence(qpysequence=changed, channel_id=0)
        assert module._qpy_sequence_hashes[0] == hashes_after_first

        module.device.sequencers[0].update_sequence.side_effect = None
        module.device.sequencers[0].update_sequence.reset_mock()
        module.upload_qpysequence(qpysequence=changed, channel_id=0)

        assert "waveforms" in module.device.sequencers[0].update_sequence.call_args.kwargs
        assert module._qpy_sequence_hashes[0] == hash_qpy_sequence_components(changed)

    def test_upload_qpysequence_full_again_after_clear_cache(self, module: QbloxModule):
        """After clear_cache the next upload is a full upload again."""
        sequence = _build_sequence([0.0, 0.1, 0.2])
        module.upload_qpysequence(qpysequence=sequence, channel_id=0)
        module.clear_cache()
        assert module._qpy_sequence_hashes == {}

        module.device.sequencers[0].sequence.reset_mock()
        module.upload_qpysequence(qpysequence=sequence, channel_id=0)
        module.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())


class TestQbloxSequencer:
    def test_to_dict(self, module: QbloxModule):
        sequencer = module.get_sequencer(0)
        as_dict = sequencer.to_dict()
        assert isinstance(as_dict, dict)


class TestQbloxFilter:
    def test_to_dict(self, module: QbloxModule):
        test_filter = module.get_filter(0)
        as_dict = test_filter.to_dict()
        assert isinstance(as_dict, dict)