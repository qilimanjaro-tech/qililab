from unittest.mock import MagicMock, PropertyMock, patch

from qblox_instruments.qcodes_drivers import Cluster as QcodesCluster
from qblox_instruments.types import ClusterType
from qcodes.instrument.base import InstrumentBase
from qcodes.instrument.channel import InstrumentModule

from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm

NUM_SLOTS = 20
DUMMY_CFG = {"1": ClusterType.CLUSTER_QCM_RF}


class QCodesCluster:
    def __init__(self, name, identifier, **kwargs):
        self.name = name
        self.identifier = identifier
        self.submodules = {}
        for i in range(1, NUM_SLOTS + 1):
            self.submodules[str(i)] = ClusterType.CLUSTER_QCM_RF

    def add_submodule(self, module_name, module):
        self.submodules[module_name] = module


class TestCluster:
    """Unit tests checking the Cluster attributes and methods"""

    def test_init_with_dummy_cfg(self):
        cluster = Cluster(name="test_dummy", dummy_cfg=DUMMY_CFG)
        submodules = cluster.submodules

        expected_submodules_ids = ["module{}".format(id) for id in list(DUMMY_CFG.keys())]
        result_submodules_ids = list(submodules.keys())
        assert len(result_submodules_ids) == len(expected_submodules_ids)
        assert all(isinstance(submodules[id], QcmQrm) for id in result_submodules_ids)
        assert all([expected_id in result_submodules_ids for expected_id in expected_submodules_ids])

    @patch("qililab.drivers.instruments.qblox.cluster.QcodesCluster.__init__")
    @patch("qililab.drivers.instruments.qblox.cluster.QcmQrm")
    def test_init_without_dummy_cfg(self, mock_qcm_qrm, mock_qcodes_cluster):
        # we need to magic mock all properties and methods we want to avoid calling in the superclass
        # a real call will produce connectivity errors
        Cluster._num_slots = 20
        Cluster.add_submodule = MagicMock()
        Cluster.parameters = {}
        Cluster.name = "Cluster"
        cluster = Cluster(name="test", address="test_address")

        assert cluster.submodules == {}
        assert cluster.instrument_modules == {}
        assert cluster._channel_lists == {}
        assert mock_qcm_qrm.call_count == 20
        assert Cluster.add_submodule.call_count == 20

        call_args = [(cluster, f"module{idx}", idx) for idx in range(1, NUM_SLOTS + 1)]
        call_args_cluster_init = (("test",), {"identifier": "test_address"})
        real_call_args = [c.args for c in mock_qcm_qrm.call_args_list]
        real_call_args_cluster_init = mock_qcodes_cluster.call_args

        assert real_call_args == call_args
        assert real_call_args_cluster_init == call_args_cluster_init
