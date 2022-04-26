from qililab.constants import DEFAULT_EXPERIMENT_NAME, DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment


def test_experiment():
    """Test experiment"""
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, experiment_name=DEFAULT_EXPERIMENT_NAME)

    return experiment
