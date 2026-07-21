"""Tests for the Qblox Module class."""
from unittest.mock import MagicMock

import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxQCM
from qililab.platform import Platform
from qililab.data_management import build_platform
from qililab.typings import DistortionState, Parameter
from typing import cast
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qblox_instruments.qcodes_drivers.module import Module as QcmQrm


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
        "marker_ovr_value",
        "offset_awg_path0",
        "offset_awg_path1"
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
        assert qcm.is_awg()
        assert not qcm.is_adc()
        assert len(qcm.awg_sequencers) == 2  # As per the YAML config
        assert qcm.out_offsets == [0.0, 0.1, 0.2, 0.3]
        filter = qcm.get_filter(0)
        assert filter.exponential_amplitude[0] == 0.31
        assert filter.exponential_time_constant[0] == 200
        assert filter.exponential_state == ['enabled', "enabled", "bypassed", None]
        assert filter.fir_coeff == [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4]
        assert filter.fir_state == "enabled"
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

    def test_init_raises_error(self):
        with pytest.raises(ValueError):
            _ = build_platform(runcard="tests/instruments/qblox/qblox_qcm_too_many_sequencers_runcard.yaml")

    def test_module_type(self, qcm: QbloxQCM):
        _ = qcm.module_type()
        qcm.device.module_type.assert_called_once()

    def test_initial_setup(self, qcm: QbloxQCM):
        """Test the initial setup of the QCM module."""
        qcm.initial_setup()

        # Verify the correct setup calls were made on the device
        qcm.device.disconnect_outputs.assert_called_once()
        for sequencer in qcm.awg_sequencers:
            qcm.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)
