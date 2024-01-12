"""Tests for the QbloxQRMRF class."""
from dataclasses import asdict
from unittest.mock import MagicMock

import pytest
from qblox_instruments.qcodes_drivers.cluster import Cluster
from qblox_instruments.types import ClusterType

from qililab.instruments.qblox import QbloxQRMRF
from qililab.typings import Parameter


@pytest.fixture(name="settings")
def fixture_settings():
    return {
        "alias": "test",
        "firmware": "0.7.0",
        "num_sequencers": 1,
        "out0_in0_lo_freq": 3e9,
        "out0_in0_lo_en": True,
        "out0_att": 34,
        "in0_att": 28,
        "out0_offset_path0": 0.123,
        "out0_offset_path1": 1.234,
        "acquisition_delay_time": 100,
        "awg_sequencers": [
            {
                "identifier": 0,
                "bus_alias": "feedline_input",
                "qubit": 0,
                "output_i": 1,
                "output_q": 0,
                "weights_i": [1, 1, 1, 1],
                "weights_q": [1, 1, 1, 1],
                "weighed_acq_enabled": False,
                "threshold": 0.5,
                "threshold_rotation": 45.0,
                "num_bins": 1,
                "intermediate_frequency": 20000000,
                "gain_i": 0.001,
                "gain_q": 0.02,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_i": 0,
                "offset_q": 0,
                "hardware_modulation": True,
                "scope_acquire_trigger_mode": "sequencer",
                "scope_hardware_averaging": True,
                "sampling_rate": 1000000000,
                "integration_length": 8000,
                "integration_mode": "ssb",
                "sequence_timeout": 1,
                "acquisition_timeout": 1,
                "hardware_demodulation": True,
                "scope_store_enabled": True,
            }
        ],
    }


class TestInitialization:
    """Unit tests for the initialization of the QbloxQRMRF class."""

    def test_init(self, settings):
        """Test the __init__ method."""
        qcm_rf = QbloxQRMRF(settings=settings)
        for name, value in settings.items():
            if name == "awg_sequencers":
                for i, sequencer in enumerate(value):
                    for seq_name, seq_value in sequencer.items():
                        assert getattr(qcm_rf.awg_sequencers[i], seq_name) == seq_value
            else:
                assert getattr(qcm_rf.settings, name) == value


class TestMethods:
    """Unit tests for the methods of the QbloxQRMRF class."""

    def test_initial_setup(self, settings):
        """Test the `initial_setup` method of the QbloxQRMRF class."""
        qcm_rf = QbloxQRMRF(settings=settings)
        qcm_rf.device = MagicMock()
        qcm_rf.initial_setup()
        assert qcm_rf.device.set.call_count == 6
        call_args = {call[0] for call in qcm_rf.device.set.call_args_list}
        assert call_args == {
            ("out0_in0_lo_freq", 3e9),
            ("out0_in0_lo_en", True),
            ("out0_att", 34),
            ("in0_att", 28),
            ("out0_offset_path0", 0.123),
            ("out0_offset_path1", 1.234),
        }

    def test_setup(self, settings):
        """Test the `setup` method of the QbloxQRMRF class."""
        qcm_rf = QbloxQRMRF(settings=settings)
        qcm_rf.device = MagicMock()
        qcm_rf.setup(parameter=Parameter.OUT0_IN0_LO_FREQ, value=3.8e9)
        qcm_rf.device.set.assert_called_once_with("out0_in0_lo_freq", 3.8e9)
        qcm_rf.setup(parameter=Parameter.GAIN, value=1)
        qcm_rf.device.sequencers[0].gain_awg_path0.assert_called_once_with(1)
        qcm_rf.device.sequencers[0].gain_awg_path1.assert_called_once_with(1)

    def test_setup_no_instrument_connection(self, settings):
        """Test the `setup` method of the QbloxQRMRF class."""
        qcm_rf = QbloxQRMRF(settings=settings)

        qcm_rf.setup(parameter=Parameter.OUT0_IN0_LO_FREQ, value=2.8e9)
        assert qcm_rf.get_parameter(parameter=Parameter.OUT0_IN0_LO_FREQ) == 2.8e9
        assert not hasattr(qcm_rf, "device")

        qcm_rf.setup(parameter=Parameter.GAIN, value=1)
        assert qcm_rf.get_parameter(parameter=Parameter.GAIN, channel_id=0)[0] == 1
        assert not hasattr(qcm_rf, "device")


class TestIntegration:
    """Integration tests of the QbloxQRMRF class."""

    def test_initial_setup(self, settings):
        """Test the `initial_setup` method of the QbloxQRMRF class."""
        qrm_rf = QbloxQRMRF(settings=settings)
        cluster = Cluster(name="test", dummy_cfg={"1": ClusterType.CLUSTER_QRM_RF})
        qrm_rf.device = cluster.modules[0]
        qrm_rf.initial_setup()
        assert qrm_rf.device.get("out0_att") == settings["out0_att"]
        assert qrm_rf.device.get("in0_att") == settings["in0_att"]
        cluster.close()

    def test_initial_setup_no_connected(self, settings):
        """Test initial setup method without connection"""
        qcm_rf = QbloxQRMRF(settings=settings)
        with pytest.raises(AttributeError, match="Instrument Device has not been initialized"):
            qcm_rf.initial_setup()

    @pytest.mark.xfail
    def test_initial_setup_with_failing_setters(self, settings):
        """Test the `initial_setup` method of the QbloxQRMRF class with the attributes
        that don't get updated in the version 0.8.1 of the `qblox_instruments`."""
        # This test is marked as `xfail` because the setters for the attributes that are
        # asserted below don't work properly in the version 0.8.1 of the `qblox_instruments` package.
        # Once this problem is fixed, this test should fail and the `xfail` mark should be removed.
        qrm_rf = QbloxQRMRF(settings=settings)
        cluster = Cluster(name="test", dummy_cfg={"1": ClusterType.CLUSTER_QRM_RF})
        qrm_rf.device = cluster.modules[0]
        qrm_rf.initial_setup()
        cluster.close()
        assert qrm_rf.device.out0_in0_lo_freq() == settings["out0_in0_lo_freq"]
        assert qrm_rf.device.out0_in0_lo_en() == settings["out0_in0_lo_en"]
        assert qrm_rf.device.out0_offset_path0() == settings["out0_offset_path0"]
        assert qrm_rf.device.out0_offset_path1() == settings["out0_offset_path1"]

    def test_setup(self, settings):
        """Test the `setup` method of the QbloxQRMRF class."""
        qrm_rf = QbloxQRMRF(settings=settings)
        cluster = Cluster(name="test", dummy_cfg={"1": ClusterType.CLUSTER_QRM_RF})
        qrm_rf.device = cluster.modules[0]
        qrm_rf.setup(parameter=Parameter.OUT0_ATT, value=58)
        assert qrm_rf.device.get("out0_att") == 58
        qrm_rf.setup(parameter=Parameter.GAIN, value=0.123)
        assert qrm_rf.device.sequencers[0].get("gain_awg_path0") == pytest.approx(0.123)
        assert qrm_rf.device.sequencers[0].get("gain_awg_path1") == pytest.approx(0.123)
        cluster.close()

    def test_setup_no_set_instrument(self, settings):
        """Test the `setup` method of the QbloxQRMRF class."""
        qrm_rf = QbloxQRMRF(settings=settings)

        qrm_rf.setup(parameter=Parameter.OUT0_ATT, value=58)
        assert qrm_rf.get_parameter(parameter=Parameter.OUT0_ATT) == 58
        assert not hasattr(qrm_rf, "device")

        qrm_rf.setup(parameter=Parameter.GAIN, value=0.123)
        assert qrm_rf.get_parameter(parameter=Parameter.GAIN, channel_id=0)[0] == 0.123
        assert not hasattr(qrm_rf, "device")

    def test_setup_with_lo_frequency(self, settings):
        """Test the `setup` method when using the `Parameter.LO_FREQUENCY` generic parameter."""
        sequencer_idx = 0
        qcm_rf = QbloxQRMRF(settings=settings)
        qcm_rf.device = MagicMock()
        qcm_rf.setup(parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=sequencer_idx)
        qcm_rf.device.set.assert_called_once_with(Parameter.OUT0_IN0_LO_FREQ, 2e9)

    def test_setup_with_lo_frequency_no_set_instrument(self, settings):
        """Test the `setup` method when using the `Parameter.LO_FREQUENCY` generic parameter."""
        sequencer_idx = 0
        qrm_rf = QbloxQRMRF(settings=settings)
        qrm_rf.setup(parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=sequencer_idx)
        assert qrm_rf.get_parameter(parameter=Parameter.LO_FREQUENCY, channel_id=0) == 2e9
        assert not hasattr(qrm_rf, "device")

    def test_to_dict_method(self, settings):
        """Test that the `to_dict` method does not return a dictionary containing the key 'out_offsets' for a correct serialization"""
        qrm_rf = QbloxQRMRF(settings=settings)
        qrm_rf.settings.out_offsets = 0.0
        assert "out_offsets" in asdict(qrm_rf.settings)
        assert "out_offsets" not in qrm_rf.to_dict()
