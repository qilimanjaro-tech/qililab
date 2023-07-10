"""Tests for the QbloxQCMRF class."""
from unittest.mock import MagicMock

import pytest
from qblox_instruments.qcodes_drivers.cluster import Cluster
from qblox_instruments.types import ClusterType

from qililab.instruments import QbloxQCMRF
from qililab.typings import Parameter


@pytest.fixture(name="settings")
def fixture_settings():
    return {
        "alias": "test",
        "id_": 0,
        "category": "awg",
        "firmware": "0.7.0",
        "num_sequencers": 1,
        "out0_lo_freq": 3.7e9,
        "out0_lo_en": True,
        "out0_att": 10,
        "out0_offset_path0": 0.2,
        "out0_offset_path1": 0.07,
        "out1_lo_freq": 3.9e9,
        "out1_lo_en": True,
        "out1_att": 6,
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
            }
        ],
    }


class TestInitialization:
    """Unit tests for the initialization of the QbloxQCMRF class."""

    def test_init(self, settings):
        """Test the __init__ method."""
        qcm_rf = QbloxQCMRF(settings=settings)
        for name, value in settings.items():
            if name == "awg_sequencers":
                for i, sequencer in enumerate(value):
                    for seq_name, seq_value in sequencer.items():
                        assert getattr(qcm_rf.awg_sequencers[i], seq_name) == seq_value
            else:
                assert getattr(qcm_rf.settings, name) == value


class TestMethods:
    """Unit tests for the methods of the QbloxQCMRF class."""

    def test_initial_setup(self, settings):
        """Test the `initial_setup` method of the QbloxQCMRF class."""
        qcm_rf = QbloxQCMRF(settings=settings)
        qcm_rf.device = MagicMock()
        qcm_rf.initial_setup()
        qcm_rf.device.set.call_count == 10
        call_args = {call[0] for call in qcm_rf.device.set.call_args_list}
        assert call_args == {
            ("out0_lo_freq", 3700000000.0),
            ("out0_lo_en", True),
            ("out0_att", 10),
            ("out0_offset_path0", 0.2),
            ("out0_offset_path1", 0.07),
            ("out1_lo_freq", 3900000000.0),
            ("out1_lo_en", True),
            ("out1_att", 6),
            ("out1_offset_path0", 0.1),
            ("out1_offset_path1", 0.6),
        }

    def test_setup(self, settings):
        """Test the `setup` method of the QbloxQCMRF class."""
        qcm_rf = QbloxQCMRF(settings=settings)
        qcm_rf.device = MagicMock()
        qcm_rf.setup(parameter=Parameter.OUT0_LO_FREQ, value=3.8e9)
        qcm_rf.device.set.assert_called_once_with("out0_lo_freq", 3.8e9)
        qcm_rf.setup(parameter=Parameter.GAIN, value=1)
        qcm_rf.device.sequencers[0].gain_awg_path0.assert_called_once_with(1)
        qcm_rf.device.sequencers[0].gain_awg_path1.assert_called_once_with(1)


class TestIntegration:
    """Integration tests of the QbloxQCMRF class."""

    def test_initial_setup(self, settings):
        """Test the `initial_setup` method of the QbloxQCMRF class."""
        qcm_rf = QbloxQCMRF(settings=settings)
        cluster = Cluster(name="test", dummy_cfg={"1": ClusterType.CLUSTER_QCM_RF})
        qcm_rf.device = cluster.modules[0]
        qcm_rf.initial_setup()
        assert qcm_rf.device.get("out0_att") == settings["out0_att"]
        assert qcm_rf.device.get("out1_att") == settings["out1_att"]
        cluster.close()

    @pytest.mark.xfail
    def test_initial_setup_with_failing_setters(self, settings):
        """Test the `initial_setup` method of the QbloxQCMRF class with the attributes
        that don't get updated in the version 0.8.1 of the `qblox_instruments`."""
        # This test is marked as `xfail` because the setters for the attributes that are
        # asserted below don't work properly in the version 0.8.1 of the `qblox_instruments` package.
        # Once this problem is fixed, this test should fail and the `xfail` mark should be removed.
        qcm_rf = QbloxQCMRF(settings=settings)
        cluster = Cluster(name="test", dummy_cfg={"1": ClusterType.CLUSTER_QCM_RF})
        qcm_rf.device = cluster.modules[0]
        qcm_rf.initial_setup()
        cluster.close()
        assert qcm_rf.device.out0_lo_freq() == settings["out0_lo_freq"]
        assert qcm_rf.device.out0_lo_en() == settings["out0_lo_en"]
        assert qcm_rf.device.out0_offset_path0() == settings["out0_offset_path0"]
        assert qcm_rf.device.out0_offset_path1() == settings["out0_offset_path1"]
        assert qcm_rf.device.out1_lo_freq() == settings["out1_lo_freq"]
        assert qcm_rf.device.out1_lo_en() == settings["out1_lo_en"]
        assert qcm_rf.device.out1_offset_path0() == settings["out1_offset_path0"]
        assert qcm_rf.device.out1_offset_path1() == settings["out1_offset_path1"]

    def test_setup(self, settings):
        """Test the `setup` method of the QbloxQCMRF class."""
        qcm_rf = QbloxQCMRF(settings=settings)
        cluster = Cluster(name="test", dummy_cfg={"1": ClusterType.CLUSTER_QCM_RF})
        qcm_rf.device = cluster.modules[0]
        qcm_rf.setup(parameter=Parameter.OUT0_ATT, value=58)
        assert qcm_rf.device.get("out0_att") == 58
        qcm_rf.setup(parameter=Parameter.GAIN, value=0.123)
        assert qcm_rf.device.sequencers[0].get("gain_awg_path0") == pytest.approx(0.123)
        assert qcm_rf.device.sequencers[0].get("gain_awg_path1") == pytest.approx(0.123)
        cluster.close()

    def test_setup_with_lo_frequency_output0(self, settings):
        """Test the `setup` method when using the `Parameter.LO_FREQUENCY` generic parameter."""
        sequencer_idx = 0
        qcm_rf = QbloxQCMRF(settings=settings)
        sequencer = qcm_rf._get_sequencer_by_id(sequencer_idx)
        sequencer.output_i = 0
        sequencer.output_q = 1
        qcm_rf.device = MagicMock()
        qcm_rf.setup(parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=sequencer_idx)
        qcm_rf.device.set.assert_called_once_with("out0_lo_freq", 2e9)

    def test_setup_with_lo_frequency_output1(self, settings):
        """Test the `setup` method when using the `Parameter.LO_FREQUENCY` generic parameter."""
        sequencer_idx = 0
        qcm_rf = QbloxQCMRF(settings=settings)
        sequencer = qcm_rf._get_sequencer_by_id(sequencer_idx)
        sequencer.output_i = 3
        sequencer.output_q = 2
        qcm_rf.device = MagicMock()
        qcm_rf.setup(parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=sequencer_idx)
        qcm_rf.device.set.assert_called_once_with("out1_lo_freq", 2e9)

    def test_setup_with_lo_frequency_without_channel_id_raises_error(self, settings):
        """Test that calling `setup` when using the `Parameter.LO_FREQUENCY` generic parameter without
        a channel id raises an error."""
        qcm_rf = QbloxQCMRF(settings=settings)
        qcm_rf.device = MagicMock()
        with pytest.raises(ValueError, match="`channel_id` cannot be None when setting the `LO_FREQUENCY` parameter"):
            qcm_rf.setup(parameter=Parameter.LO_FREQUENCY, value=2e9)

    def test_setup_with_lo_frequency_with_2_los(self, settings):
        """Test that calling `setup` with `Parameter.LO_FREQUENCY` when the sequencer is connected to
        2 LOs raises an error."""
        sequencer_idx = 0
        qcm_rf = QbloxQCMRF(settings=settings)
        sequencer = qcm_rf._get_sequencer_by_id(sequencer_idx)
        sequencer.output_i = 0
        sequencer.output_q = 2
        qcm_rf.device = MagicMock()
        with pytest.raises(
            ValueError,
            match=f"Cannot set the LO frequency of sequencer {sequencer_idx} because it is connected to two LOs. ",
        ):
            qcm_rf.setup(parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=sequencer_idx)
