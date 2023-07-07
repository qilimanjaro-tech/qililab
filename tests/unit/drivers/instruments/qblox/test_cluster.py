from unittest.mock import MagicMock

import pytest
from qblox_instruments.types import ClusterType
from qcodes import Instrument
from qcodes.tests.instrument_mocks import DummyChannel, DummyInstrument

from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

NUM_SLOTS = 20
NUM_SEQUENCERS = 6
DUMMY_CFG = {"1": ClusterType.CLUSTER_QCM_RF}
PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name


class MockQcmQrm(DummyChannel):
    """Mock class for QcmQrm"""

    def __init__(self, parent, name, slot_idx, **kwargs):
        """Mock init method"""

        super().__init__(parent=parent, name=name, channel="", **kwargs)

        # Store sequencer index
        self._slot_idx = slot_idx
        self.submodules = {"test_submodule": MagicMock()}
        self.is_qcm_type = True
        self.is_qrm_type = False
        self.is_rf_type = False

    def arm_sequencer(self):
        """Mock arm_sequencer method"""

        return None

    def start_sequencer(self):
        """Mock start_sequencer method"""

        return None


class MockCluster(DummyInstrument):
    """Mock class for Cluster"""

    def __init__(self, name, identifier=None, **kwargs):
        """Mock init method"""

        super().__init__(name, **kwargs)

        self.address = identifier
        self._num_slots = 20
        self.submodules = {"test_submodule": MagicMock()}
        self._present_at_init = MagicMock()


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )
    pulse_event = PulseEvent(pulse=pulse, start_time=0)
    return PulseBusSchedule(timeline=[pulse_event], port=0)


class TestCluster:
    """Unit tests checking the Cluster attributes and methods. These tests mock the parent class of the `Cluster`,
    such that the code from `qcodes` is never executed."""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_qcm_qrm_bases = QcmQrm.__bases__
        cls.old_cluster_bases = Cluster.__bases__
        QcmQrm.__bases__ = (MockQcmQrm,)
        Cluster.__bases__ = (MockCluster,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        QcmQrm.__bases__ = cls.old_qcm_qrm_bases
        Cluster.__bases__ = cls.old_cluster_bases

    def test_init_without_dummy_cfg(self):
        """Test init method without dummy configuration"""
        cluster_name = "test_cluster_without_dummy"
        cluster = Cluster(name=cluster_name)
        cluster_submodules = cluster.submodules
        qcm_qrm_idxs = list(cluster_submodules.keys())
        cluster_submodules_expected_names = [f"{cluster_name}_module{idx}" for idx in range(1, NUM_SLOTS + 1)]
        cluster_registered_names = [cluster_submodules[idx].name for idx in qcm_qrm_idxs]

        assert len(cluster_submodules) == NUM_SLOTS
        assert all(isinstance(cluster_submodules[qcm_qrm_idx], QcmQrm) for qcm_qrm_idx in qcm_qrm_idxs)
        assert cluster_submodules_expected_names == cluster_registered_names


class TestClusterIntegration:
    """Integration tests for the Cluster class. These tests use the `dummy_cfg` attribute to be able to use the
    code from qcodes (without mocking the parent class)."""

    @classmethod
    def teardown_method(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()

    def test_init_with_dummy_cfg(self):
        """Test init method with dummy configuration"""

        cluster = Cluster(name="test_cluster_dummy", dummy_cfg=DUMMY_CFG)
        submodules = cluster.submodules

        expected_submodules_ids = [f"module{id}" for id in list(DUMMY_CFG.keys())]
        result_submodules_ids = list(submodules.keys())
        assert len(result_submodules_ids) == len(expected_submodules_ids)
        assert all(isinstance(submodules[id], QcmQrm) for id in result_submodules_ids)
        assert result_submodules_ids == expected_submodules_ids


class TestQcmQrm:
    """Unit tests checking the QililabQcmQrm attributes and methods"""

    def test_init_qcm_type(self):
        """Test init method for QcmQrm for a QCM module."""

        parent = MagicMock()

        # Set qcm/qrm attributes
        parent._is_qcm_type.return_value = True
        parent._is_qrm_type.return_value = False

        qcm_qrn_name = "qcm_qrm"
        qcm_qrm = QcmQrm(parent=parent, name=qcm_qrn_name, slot_idx=0)

        submodules = qcm_qrm.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{qcm_qrn_name}_sequencer{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SEQUENCERS
        assert all(isinstance(submodules[seq_idx], SequencerQCM) for seq_idx in seq_idxs)
        assert expected_names == registered_names

    def test_init_qrm_type(self):
        """Test init method for QcmQrm for a QRM module."""

        parent = MagicMock()

        # Set qcm/qrm attributes
        parent._is_qcm_type.return_value = False
        parent._is_qrm_type.return_value = True

        qcm_qrn_name = "qcm_qrm"
        qcm_qrm = QcmQrm(parent=parent, name=qcm_qrn_name, slot_idx=0)

        submodules = qcm_qrm.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{qcm_qrn_name}_sequencer{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SEQUENCERS
        assert all(isinstance(submodules[seq_idx], SequencerQRM) for seq_idx in seq_idxs)
        assert expected_names == registered_names
