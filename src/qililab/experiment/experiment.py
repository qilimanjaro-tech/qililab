"""Experiment class."""
from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.experiment.utils import ExperimentDict
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.settings import SETTINGS_MANAGER, ExperimentSettings


class Experiment:
    """Execution class"""

    platform: Platform
    execution: Execution
    settings: ExperimentSettings

    def __init__(self, experiment_name: str, platform_name: str):
        experiment_dict = self._load_settings(experiment_name=experiment_name, platform_name=platform_name)
        self.settings = ExperimentSettings(**experiment_dict.settings)
        self.platform = PLATFORM_MANAGER_DB.build(platform_name=platform_name)
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulses=experiment_dict.pulses)

    def execute(self):
        """Run execution."""
        return self.execution.execute(settings=self.settings)

    def draw(self, resolution: float = 1.0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution)

    @property
    def hardware_average(self):
        """Execution 'hardware_average' property.

        Returns:
            int: settings.hardware_average.
        """
        return self.settings.hardware_average

    @property
    def software_average(self):
        """Execution 'software_average' property.

        Returns:
            int: settings.software_average.
        """
        return self.settings.software_average

    @property
    def repetition_duration(self):
        """Execution 'repetition_duration' property.

        Returns:
            int: settings.repetition_duration.
        """
        return self.settings.repetition_duration

    @property
    def delay_between_pulses(self):
        """Execution 'delay_between_pulses' property.

        Returns:
            int: settings.delay_between_pulses.
        """
        return self.settings.delay_between_pulses

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
        return ExperimentDict(**settings)
