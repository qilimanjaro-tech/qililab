"""Tests for the Qblox Module class."""

from typing import cast
from unittest.mock import MagicMock

import pytest
from qblox_instruments.qcodes_drivers.module import Module as QcmQrm
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.data_management import build_platform
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.qblox import QbloxModule
from qililab.platform import Platform
from qililab.qprogram.qblox_compiler import AcquisitionData
from qililab.typings import AcquireTriggerMode, IntegrationMode, Parameter

@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    InstrumentFactory.register(QbloxModule)
    return build_platform(runcard="tests/instruments/qblox/module_runcard.yaml")


@pytest.fixture(name="module")
def fixture_module(platform: Platform) -> QbloxModule:
    module = cast(QbloxModule, platform.get_element(alias="module"))

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
    def test_get_filter(self, module: QbloxModule):
        pass

    def test_(self, module: QbloxModule):
        pass

    def test_initial_setup(self, module: QbloxModule):
        """Test the initial setup of the QCM module."""
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

    def test_reset(self, module: QbloxModule):
        """Test resetting the QCM module."""
        module.reset()

        module.device.reset.assert_called_once()
        assert module.cache == {}
        assert module.sequences == {}

    def test_turn_off(self, module: QbloxModule):
        module.turn_off()

        assert module.device.stop_sequencer.call_count == 2

    def test_upload(self, module: QbloxModule):
        """Test uploading a QpySequence to the QCM module."""
        module.sequences[0] = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        module.upload(channel_id=0)

        module.device.sequencers[0].sequence.assert_called_once_with(module.sequences[0].todict())
        module.device.sequencers[0].sync_en.assert_called_once_with(True)

    def test_upload_qpysequence(self, module: QbloxModule):
        """Test uploading a QpySequence to the QCM module."""
        sequence = Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())
        module.upload_qpysequence(qpysequence=sequence, channel_id=0)

        module.device.sequencers[0].sequence.assert_called_once_with(sequence.todict())