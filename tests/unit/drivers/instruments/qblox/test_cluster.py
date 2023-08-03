from unittest.mock import MagicMock

import pytest
from qblox_instruments.types import ClusterType
from qcodes import Instrument
from qcodes import validators as vals
from qcodes.instrument import DelegateParameter
from qcodes.tests.instrument_mocks import DummyChannel, DummyInstrument

from qililab.drivers import parameters
from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm, QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

NUM_SLOTS = 20
PRESENT_SUBMODULES = [2, 4, 6, 8, 10, 12, 16, 18, 20]
NUM_SEQUENCERS = 6
DUMMY_CFG = {1: ClusterType.CLUSTER_QCM_RF}
PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name


class MockQcmQrm(DummyChannel):
    """Mock class for QcmQrm"""

    is_rf_type = False

    def __init__(self, parent, name, slot_idx, **kwargs):
        """Mock init method"""

        super().__init__(parent=parent, name=name, channel="", **kwargs)

        # Store sequencer index
        self._slot_idx = slot_idx
        self.submodules = {"test_submodule": MagicMock()}
        self.is_qcm_type = True
        self.is_qrm_type = False
        self.is_rf_type = False

        self.add_parameter(
            name="present",
            label="Present",
            unit=None,
            get_cmd=None,
            set_cmd=None,
            get_parser=bool,
            vals=vals.Numbers(0, 20e9),
        )
        self.set("present", True if slot_idx % 2 == 0 else False)

    def arm_sequencer(self):
        """Mock arm_sequencer method"""

        return None

    def start_sequencer(self):
        """Mock start_sequencer method"""

        return None


class MockCluster(DummyInstrument):  # pylint: disable=abstract-method
    """Mock class for Cluster"""

    is_rf_type = True

    def __init__(self, name, identifier=None, **kwargs):
        """Mock init method"""

        super().__init__(name, **kwargs)
        self.is_rf_type = True
        self.address = identifier
        self._num_slots = 20
        self.submodules = {}
        for idx in range(1, NUM_SLOTS + 1):
            self.submodules[f"module{idx}"] = MockQcmQrm(parent=self, name=f"module{idx}", slot_idx=idx)

    def _present_at_init(self, slot_idx: int):
        """Mock _present_at_init method"""
        return True if slot_idx in PRESENT_SUBMODULES else False


class MockQcmQrmRF(DummyInstrument):  # pylint: disable=abstract-method
    is_rf_type = True

    def __init__(self, name, qcm_qrm, parent=None, slot_idx=0):  # pylint: disable=unused-argument
        super().__init__(name=name, gates=["dac1"])

        # local oscillator parameters
        lo_channels = ["out0_in0"] if qcm_qrm == "qrm" else ["out0", "out1"]
        for channel in lo_channels:
            self.add_parameter(
                name=f"{channel}_lo_freq",
                label="Frequency",
                unit="Hz",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )
            self.add_parameter(
                f"{channel}_lo_en",
                label="Status",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )

        # attenuator parameters
        att_channels = ["out0", "in0"] if qcm_qrm == "qrm" else ["out0", "out1"]
        for channel in att_channels:
            self.add_parameter(
                name=f"{channel}_att",
                label="Attenuation",
                unit="dB",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )


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

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init_without_dummy_cfg(self):
        """Test init method without dummy configuration"""
        cluster_name = "test_cluster_without_dummy"
        cluster = Cluster(name=cluster_name)
        cluster_submodules = cluster.submodules
        qcm_qrm_idxs = list(cluster_submodules.keys())
        cluster_submodules_expected_names = [f"{cluster_name}_module{idx}" for idx in range(1, NUM_SLOTS + 1)]
        cluster_registered_names = [cluster_submodules[idx].name for idx in qcm_qrm_idxs]
        present_idxs = [slot_idx - 1 for slot_idx in range(1, 20) if cluster._present_at_init(slot_idx)]
        present_names = [qcm_qrm_idxs[idx] for idx in present_idxs]

        assert len(cluster_submodules) == NUM_SLOTS
        assert all(isinstance(cluster_submodules[idx], QcmQrm) for idx in present_names)
        non_present_modules = [
            cluster_submodules[f"module{idx}"] for idx in range(1, NUM_SLOTS + 1) if idx not in PRESENT_SUBMODULES
        ]
        assert all(isinstance(module, MockQcmQrm) for module in non_present_modules)
        assert cluster_submodules_expected_names == cluster_registered_names


class TestClusterIntegration:
    """Integration tests for the Cluster class. These tests use the `dummy_cfg` attribute to be able to use the
    code from qcodes (without mocking the parent class)."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""

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
        parent._is_rf_type.return_value = False

        qcm_qrm_name = "qcm_qrm"
        qcm_qrm = QcmQrm(parent=parent, name=qcm_qrm_name, slot_idx=0)

        submodules = qcm_qrm.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{qcm_qrm_name}_sequencer{idx}" for idx in range(6)]
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
        parent._is_rf_type.return_value = False

        qcm_qrn_name = "qcm_qrm"
        qcm_qrm = QcmQrm(parent=parent, name=qcm_qrn_name, slot_idx=0)

        submodules = qcm_qrm.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{qcm_qrn_name}_sequencer{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SEQUENCERS
        assert all(isinstance(submodules[seq_idx], SequencerQRM) for seq_idx in seq_idxs)
        assert expected_names == registered_names

    @pytest.mark.parametrize(
        ("qrm_qcm", "channels"),
        [
            ("qrm", ["out0_in0_lo_freq", "out0_in0_lo_en", "out0_att", "in0_att"]),
            ("qcm", ["out0_lo_freq", "out0_lo_en", "out1_lo_freq", "out1_lo_en", "out0_att", "out1_att"]),
        ],
    )
    def test_init_rf_modules(self, qrm_qcm, channels):
        """Test init for the lo and attenuator in the rf instrument"""

        parent = MagicMock()

        # Set qcm/qrm attributes
        parent._is_rf_type.return_value = True
        parent._is_qcm_type.return_value = qrm_qcm == "qcm"
        parent._is_qrm_type.return_value = qrm_qcm == "qrm"

        qcm_qrm_rf = "qcm_qrm_rf"
        qcm_qrm_rf = QcmQrm(parent=parent, name=qcm_qrm_rf, slot_idx=0)

        assert all((channel in qcm_qrm_rf.parameters for channel in channels))


class TestQcmQrmRFModules:
    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    @pytest.mark.parametrize(
        "channel",
        ["out0_in0", "out0", "out1"],
    )
    def test_qcm_qrm_rf_lo(self, channel):
        qcm_qrm = "qrm" if channel == "out0_in0" else "qcm"
        MockQcmQrmRF.is_qrm_type = qcm_qrm == "qrm"
        MockQcmQrmRF.is_qcm_type = qcm_qrm == "qcm"

        lo_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm=qcm_qrm)
        lo = QcmQrmRfLo(name=f"test_lo_{channel}", parent=lo_parent, channel=channel)
        lo_frequency = parameters.lo.frequency
        freq_parameter = f"{channel}_lo_freq"
        assert isinstance(lo.parameters[lo_frequency], DelegateParameter)
        # test set get with frequency and lo_frequency
        lo_parent.set(freq_parameter, 2)
        assert lo.get(lo_frequency) == 2
        assert lo.lo_frequency.label == "Delegated parameter for local oscillator frequency"
        # test on and off
        lo.on()
        assert lo_parent.get(f"{channel}_lo_en") is True
        assert lo.get("status") is True
        lo.off()
        assert lo_parent.get(f"{channel}_lo_en") is False
        assert lo.get("status") is False

    @pytest.mark.parametrize(
        "channel",
        ["out0", "in0", "out1"],
    )
    def test_qcm_qrm_rf_att(self, channel):
        qcm_qrm = "qrm" if channel in ["out0", "in0"] else "qcm"
        MockQcmQrmRF.is_qrm_type = qcm_qrm == "qrm"
        MockQcmQrmRF.is_qcm_type = qcm_qrm == "qcm"

        att_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm=qcm_qrm)
        att = QcmQrmRfAtt(name=f"test_att_{channel}", parent=att_parent, channel=channel)
        attenuation = parameters.attenuator.attenuation
        att_parameter = f"{channel}_att"
        assert isinstance(att.parameters[attenuation], DelegateParameter)
        # test set get with frequency and lo_frequency
        att_parent.set(att_parameter, 2)
        assert att.get(attenuation) == 2
        assert att.attenuation.label == "Delegated parameter for attenuation"
