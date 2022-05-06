from qililab.constants import DEFAULT_EXPERIMENT_NAME, DEFAULT_PLATFORM_NAME
from qililab.experiment import HardwareExperiment


def test_experiment():
    """Test experiment"""
    return HardwareExperiment(platform_name=DEFAULT_PLATFORM_NAME, experiment_name=DEFAULT_EXPERIMENT_NAME)
