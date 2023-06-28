from qblox_instruments.types import ClusterType
from qililab.drivers.instruments.qblox.cluster import Cluster

NUM_SLOTS = 20
DUMMY_CFG = {"1": ClusterType.CLUSTER_QCM_RF}

class TestCluster:
    """Unit tests checking the Cluster attributes and methods"""
    
    def test_init(self):
        cluster = Cluster(name="test", dummy_cfg=DUMMY_CFG)
        submodules = cluster.submodules
        
        assert len(submodules) == len(list(DUMMY_CFG.keys()))
