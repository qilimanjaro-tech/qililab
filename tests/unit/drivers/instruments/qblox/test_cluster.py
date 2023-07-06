from unittest.mock import MagicMock

import pytest
from qblox_instruments.types import ClusterType
from qcodes import Instrument
from qcodes.instrument import DelegateParameter

from qililab.drivers import parameters
from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm, QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer import AWGSequencer
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

from .mock_utils import MockCluster, MockQcmQrm, MockQCMRF, MockQRMRF

NUM_SLOTS = 20
NUM_SEQUENCERS = 6
DUMMY_CFG = {"1": ClusterType.CLUSTER_QCM_RF}
PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name


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
    """Unit tests checking the Cluster attributes and methods"""

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

        Instrument.close_all()
        QcmQrm.__bases__ = cls.old_qcm_qrm_bases
        Cluster.__bases__ = cls.old_cluster_bases

    def test_init_with_dummy_cfg(self):
        """Test init method with dummy configuration"""

        cluster = Cluster(name="test_cluster_dummy", dummy_cfg=DUMMY_CFG)
        submodules = cluster.submodules

        expected_submodules_ids = [f"module{id}" for id in list(DUMMY_CFG.keys())]
        result_submodules_ids = list(submodules.keys())
        assert len(result_submodules_ids) == len(expected_submodules_ids)
        assert all(isinstance(submodules[id], QcmQrm) for id in result_submodules_ids)
        assert result_submodules_ids == expected_submodules_ids

    def test_init_without_dummy_cfg(self):
        """Test init method without dummy configuration"""
        cluster = Cluster(name="test_cluster_without_dummy")
        cluster_submodules = cluster.submodules
        qcm_qrm_idxs = list(cluster_submodules.keys())
        cluster_submodules_expected_names = [f"module{idx}" for idx in range(1, NUM_SLOTS + 1)]
        cluster_registered_names = [cluster_submodules[idx].name for idx in qcm_qrm_idxs]

        assert len(cluster_submodules) == NUM_SLOTS
        assert all(isinstance(cluster_submodules[qcm_qrm_idx], QcmQrm) for qcm_qrm_idx in qcm_qrm_idxs)
        assert cluster_submodules_expected_names == cluster_registered_names


class TestQcmQrm:
    """Unit tests checking the QililabQcmQrm attributes and methods"""

    def test_init(self):
        """Test init method for QcmQrm"""

        qcm_qrn_name = "qcm_qrm"
        qcm_qrm = QcmQrm(parent=MagicMock(), name=qcm_qrn_name, slot_idx=0)
        submodules = qcm_qrm.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{qcm_qrn_name}_sequencer{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SEQUENCERS
        assert all(isinstance(submodules[seq_idx], AWGSequencer) for seq_idx in seq_idxs)
        assert expected_names == registered_names


class TestQcmQrmRF:
    @pytest.mark.parametrize(
        ("qrm_qcm", "channels"),
        [
            ("qrm", ["out0_in0_lo_freq", "out0_in0_lo_en", "out0_att", "in0_att"]),
            ("qcm", ["out0_lo_freq", "out0_lo_en", "out1_lo_freq", "out1_lo_en", "out0_att", "out1_att"]),
        ],
    )
    def test_init_rf_modules(self, qrm_qcm, channels):
        """Test init for the lo and attenuator in the rf instrument"""
        BaseInstrument = MockQRMRF if qrm_qcm == "qrm" else MockQCMRF
        QcmQrm.__bases__ = (BaseInstrument,)
        qcmqrm_rf = QcmQrm(parent=None, name=f"{qrm_qcm}_test_init_rf", slot_idx=0)

        assert all((channel in qcmqrm_rf.parameters.keys() for channel in channels))

        qcmqrm_rf.close()


@pytest.mark.parametrize(
    "channel",
    ["out0_in0", "out0", "out1"],
)
def test_qcmqrflo(channel):
    BaseInstrument = MockQRMRF if channel == "out0_in0" else MockQCMRF
    lo_parent = BaseInstrument(f"test_qcmqrflo_{channel}")
    lo = QcmQrmRfLo(name=f"test_lo_{channel}", parent=lo_parent, channel=channel)
    lo_frequency = parameters.lo.frequency
    freq_parameter = f"{channel}_lo_freq"
    assert isinstance(lo.parameters[lo_frequency], DelegateParameter)
    # test set get with frequency and lo_frequency
    lo_parent.set(freq_parameter, 2)
    assert lo.get(lo_frequency) == 2
    assert lo.lo_frequency.label == "Delegated parameter for local oscillator frequency"
    # close instruments
    lo_parent.close()


@pytest.mark.parametrize(
    "channel",
    ["out0", "in0", "out1"],
)
def test_qcmqrfatt(channel):
    BaseInstrument = MockQRMRF if channel in ["out0", "in0"] else MockQCMRF
    att_parent = BaseInstrument(f"test_qcmqrfatt_{channel}")
    att = QcmQrmRfAtt(name=f"test_att_{channel}", parent=att_parent, channel=channel)
    attenuation = parameters.attenuator.attenuation
    att_parameter = f"{channel}_att"
    assert isinstance(att.parameters[attenuation], DelegateParameter)
    # test set get with frequency and lo_frequency
    att_parent.set(att_parameter, 2)
    assert att.get(attenuation) == 2
    assert att.attenuation.label == "Delegated parameter for attenuation"
    att_parent.close()
