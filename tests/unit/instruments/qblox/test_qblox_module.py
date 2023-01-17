from pathlib import Path
from typing import cast

from qililab.instruments.awg_settings.awg_qblox_sequencer import AWGQbloxSequencer
from qililab.instruments.qblox import QbloxModule


class TestQBloxModule:
    """Unit tests checking the QbloxModule attributes and methods"""

    def test_initial_setup_method(self, qblox_module: QbloxModule):
        """Test initial_setup method"""
        qblox_module.initial_setup()
        for sequencer in qblox_module.awg_sequencers:
            device_sequencer = qblox_module.device.sequencers[sequencer.identifier]
            if sequencer.hardware_modulation:
                device_sequencer.mod_en_awg.assert_called_once_with(sequencer.hardware_modulation)
                device_sequencer.nco_freq.assert_called_once_with(sequencer.intermediate_frequency)
            device_sequencer.gain_awg_path0.assert_called_once_with(sequencer.gain_path0)
            device_sequencer.gain_awg_path1.assert_called_once_with(sequencer.gain_path1)
            device_sequencer.offset_awg_path0.assert_called_once_with(sequencer.offset_path0)
            device_sequencer.offset_awg_path1.assert_called_once_with(sequencer.offset_path1)
            device_sequencer.sync_en.assert_called_once_with(cast(AWGQbloxSequencer, sequencer).sync_enabled)
            device_sequencer.mixer_corr_gain_ratio.assert_called_once_with(sequencer.gain_imbalance)
            device_sequencer.mixer_corr_phase_offset_degree.assert_called_once_with(sequencer.phase_imbalance)
