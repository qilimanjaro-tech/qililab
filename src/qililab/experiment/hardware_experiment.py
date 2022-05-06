"""HardwareExperiment class."""
from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.experiment.utils import ExperimentSchema
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.settings import SETTINGS_MANAGER


class HardwareExperiment:
    """HardwareExperiment class"""

    platform: Platform
    execution: Execution
    _schema: ExperimentSchema

    def __init__(self, experiment_name: str, platform_name: str):
        self._schema = self._load_settings(experiment_name=experiment_name, platform_name=platform_name)
        self.platform = PLATFORM_MANAGER_DB.build(
            platform_name=platform_name, experiment_settings=self._schema.settings
        )
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulses=self._schema.pulses)

    def execute(self):
        """Run execution."""
        return self.execution.execute()

    def draw(self, resolution: float = 1.0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution)

    def _load_settings(self, experiment_name: str, platform_name: str):
        """Load experiment settings and cast them into ExperimentDict class.

        Args:
            experiment_name (str): Name of the experiment.
            platform_name (str): Name of the platform.

        Returns:
            ExperimentDict: Class containing the experiment settings.
        """
        settings = SETTINGS_MANAGER.load(
            foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform_name, filename=experiment_name
        )
        return ExperimentSchema(**settings)
