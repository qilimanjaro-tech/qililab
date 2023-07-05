from unittest.mock import MagicMock, patch

import pytest
from qblox_instruments.types import ClusterType
from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm
from qililab.drivers.instruments.qblox.sequencer import AWGSequencer
from qililab.drivers.interfaces.awg import AWG
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


class MockSequencer(DummyInstrument):
    def __init__(self, parent, name, seq_idx, **kwargs):
        super().__init__(name, **kwargs)

        # Store sequencer index
        self.seq_idx = seq_idx

        self.add_parameter(
            "channel_map_path0_out0_en",
            label="Sequencer path 0 output 0 enable",
            docstring="Sets/gets sequencer channel map enable of path 0 to " "output 0.",
            unit="",
            vals=vals.Bool(),
            set_parser=bool,
            get_parser=bool,
            set_cmd=None,
            get_cmd=None,
        )

        self.add_parameter(
            "channel_map_path1_out1_en",
            label="Sequencer path 1 output 1 enable",
            docstring="Sets/gets sequencer channel map enable of path 1 to " "output 1.",
            unit="",
            vals=vals.Bool(),
            set_parser=bool,
            get_parser=bool,
            set_cmd=None,
            get_cmd=None,
        )

        if parent.is_qcm_type:
            self.add_parameter(
                "channel_map_path0_out2_en",
                label="Sequencer path 0 output 2 enable.",
                docstring="Sets/gets sequencer channel map enable of path 0 " "to output 2.",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )

            self.add_parameter(
                "channel_map_path1_out3_en",
                label="Sequencer path 1 output 3 enable.",
                docstring="Sets/gets sequencer channel map enable of path 1 " "to output 3.",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )


class MockQcmQrm(DummyInstrument):
    def __init__(self, parent, name, slot_idx, **kwargs):
        super().__init__(name, **kwargs)

        # Store sequencer index
        self._slot_idx = slot_idx
        self.submodules = {"test_submodule": MagicMock()}
        self.is_qcm_type = True
        self.is_qrm_type = False
        self.is_rf_type = False


class MockCluster(DummyInstrument):
    def __init__(self, name, address=None, **kwargs):
        super().__init__(name)

        self.address = address
        self._num_slots = NUM_SLOTS
        self.submodules = {"test_submodule": MagicMock()}


class TestCluster:
    """Unit tests checking the Cluster attributes and methods"""

    def test_init_with_dummy_cfg(self):
        cluster = Cluster(name="test_cluster_dummy", dummy_cfg=DUMMY_CFG)
        submodules = cluster.submodules

        expected_submodules_ids = ["module{}".format(id) for id in list(DUMMY_CFG.keys())]
        result_submodules_ids = list(submodules.keys())
        assert len(result_submodules_ids) == len(expected_submodules_ids)
        assert all(isinstance(submodules[id], QcmQrm) for id in result_submodules_ids)
        assert result_submodules_ids == expected_submodules_ids

    def test_init_without_dummy_cfg(self):
        QcmQrm.__bases__ = (MockQcmQrm,)
        Cluster.__bases__ = (MockCluster,)
        AWGSequencer.__bases__ = (MockSequencer, AWG)
        qcm_qrm_name = "test_qcm_qrm"
        qcm_qrm_prefix = "module"
        sequencers_prefix = "sequencer"
        cluster = Cluster(name="test_cluster_without_dummy")
        qcm_qrm = QcmQrm(parent=cluster, name=qcm_qrm_name, slot_idx=0)
        cluster_submodules = cluster.submodules
        qcm_qrm_submodules = qcm_qrm.submodules
        qcm_qrm_idxs = list(cluster_submodules.keys())
        seq_idxs = list(qcm_qrm_submodules.keys())
        cluster_submodules_expected_names = [f"{qcm_qrm_prefix}{idx}" for idx in range(1, NUM_SLOTS + 1)]
        cluster_registered_names = [cluster_submodules[idx].name for idx in qcm_qrm_idxs]
        expected_names = [f"{sequencers_prefix}{idx}" for idx in range(6)]
        registered_names = [qcm_qrm_submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(cluster_submodules) == NUM_SLOTS
        assert all(isinstance(cluster_submodules[qcm_qrm_idx], QcmQrm) for qcm_qrm_idx in qcm_qrm_idxs)
        assert cluster_submodules_expected_names == cluster_registered_names

        assert len(qcm_qrm_submodules) == NUM_SEQUENCERS
        assert all(isinstance(qcm_qrm_submodules[seq_idx], AWGSequencer) for seq_idx in seq_idxs)
        assert expected_names == registered_names


class TestIntegration:
    """Integration tests of the Cluster class."""

    @patch("qililab.drivers.instruments.qblox.sequencer.AWGSequencer.execute")
    def test_execute(self, mock_execute, pulse_bus_schedule):
        QcmQrm.__bases__ = (MockQcmQrm,)
        Cluster.__bases__ = (MockCluster,)
        AWGSequencer.__bases__ = (MockSequencer, AWG)
        cluster = Cluster(name="test_cluster_integration")
        submodules = cluster.submodules
        result_submodules_ids = list(submodules.keys())

        for module_name in result_submodules_ids:
            qcm = cluster.submodules[module_name]
            sequencers = qcm.submodules
            for sequencer_key in sequencers.keys():
                sequencer = sequencers[sequencer_key]
                sequencer.execute(pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1)
                mock_execute.assert_called()
