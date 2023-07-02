import pytest
from qblox_instruments.types import ClusterType
from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

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
    pulse = Pulse(amplitude=PULSE_AMPLITUDE, phase=PULSE_PHASE, duration=PULSE_DURATION, frequency=PULSE_FREQUENCY, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0)
    return PulseBusSchedule(timeline=[pulse_event], port=0)

class TestCluster:
    """Unit tests checking the Cluster attributes and methods"""
    
    def test_init_with_dummy_cfg(self, pulse_bus_schedule):
        cluster = Cluster(name="test_dummy", dummy_cfg=DUMMY_CFG)
        submodules = cluster.submodules
        result_submodules_ids = list(submodules.keys())
        
        for module_name in result_submodules_ids:
            qcm = cluster.submodules[module_name]
            sequencers = qcm.submodules
            for sequencer_key in sequencers.keys():
                sequencer = sequencers[sequencer_key]
                sequencer.execute(pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1, min_wait_time=1)
        
        assert 1 == 0
        
