"""Unit tests for the QbloxQCMRF class."""
from qililab.instruments import QbloxQCMRF

settings = {
    "alias": "test",
    "id_": 0,
    "category": "awg",
    "firmware": "0.7.0",
    "num_sequencers": 1,
    "out0_lo_freq": 3.7e9,
    "out0_lo_en": True,
    "out0_att": 0.4,
    "out0_offset_path0": 0.2,
    "out0_offset_path1": 0.07,
    "out1_lo_freq": 3.9e9,
    "out1_lo_en": True,
    "out1_att": 0.345,
    "out1_offset_path0": 0.1,
    "out1_offset_path1": 0.6,
    "awg_sequencers": [
        {
            "identifier": 0,
            "chip_port_id": 0,
            "output_i": 0,
            "output_q": 1,
            "num_bins": 1,
            "intermediate_frequency": 20000000,
            "gain_i": 0.001,
            "gain_q": 0.02,
            "gain_imbalance": 1,
            "phase_imbalance": 0,
            "offset_i": 0,
            "offset_q": 0,
            "hardware_modulation": True,
            "sync_enabled": True,
        }
    ],
}


class TestQbloxQCMRF:
    """Unit tests for the QbloxQCMRF class."""

    def test_init(self):
        """Test the __init__ method."""
        qcm_rf = QbloxQCMRF(settings=settings)
        for name, value in settings.items():
            if name == "awg_sequencers":
                for i, sequencer in enumerate(value):
                    for seq_name, seq_value in sequencer.items():
                        assert getattr(qcm_rf.awg_sequencers[i], seq_name) == seq_value
            else:
                assert getattr(qcm_rf.settings, name) == value
