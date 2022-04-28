"""Test experiment."""
from unittest.mock import patch

import pytest

from qililab.constants import DEFAULT_EXPERIMENT_NAME, DEFAULT_PLATFORM_NAME
from qililab.experiment import Execution, Experiment
from qililab.platform import Platform

from ..utils.side_effect import yaml_safe_load_side_effect


@patch("qililab.settings.settings_manager.yaml.safe_load", return_value=yaml_safe_load_side_effect)
@pytest.fixture(name="experiment")
def fixture_experiment():
    """Return Experiment object."""
    return Experiment(platform_name=DEFAULT_PLATFORM_NAME, experiment_name=DEFAULT_EXPERIMENT_NAME)


class TestExperiment:
    """Unit tests checking the Experiment attributes and methods"""

    def test_platform_attribute_instance(self, experiment: Experiment):
        """Test platform attribute instance."""
        assert isinstance(experiment.platform, Platform)

    def test_execution_attribute_instance(self, experiment: Experiment):
        """Test execution attribute instance."""
        assert isinstance(experiment.execution, Execution)

    def test_run_method(self, experiment: Experiment):
        """Test run method."""
        experiment.run()
