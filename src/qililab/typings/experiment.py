""" Experiment Options Typings """

from dataclasses import asdict, dataclass, field
from typing import List

from qiboconnection.api import API

from qililab.constants import EXPERIMENT, RUNCARD
from qililab.typings.execution import ExecutionOptions
from qililab.typings.yaml_type import yaml
from qililab.utils.loop import Loop


@dataclass
class ExperimentSettings:
    """Experiment settings."""

    hardware_average: int = 1024
    software_average: int = 1
    repetition_duration: int = 200000

    def __str__(self):
        """Returns a string representation of the experiment settings."""
        return yaml.dump(asdict(self), sort_keys=False)


@dataclass
class ExperimentOptions:
    """Experiment Options"""

    loops: List[Loop] | None = None
    settings: ExperimentSettings = ExperimentSettings()
    connection: API | None = None
    device_id: int | None = None
    name: str = "experiment"
    plot_y_label: str | None = None
    remote_device_manual_override: bool = field(default=False)
    execution_options: ExecutionOptions = ExecutionOptions()

    def to_dict(self):
        """Convert Experiment into a dictionary.

        Returns:
            dict: Dictionary representation of the Experiment class.
        """
        return {
            EXPERIMENT.LOOPS: [loop.to_dict() for loop in self.loops] if self.loops is not None else None,
            RUNCARD.SETTINGS: asdict(self.settings),
            RUNCARD.NAME: self.name,
            EXPERIMENT.CONNECTION: None,
            EXPERIMENT.DEVICE_ID: self.device_id,
            EXPERIMENT.PLOT_Y_LABEL: self.plot_y_label,
            EXPERIMENT.REMOTE_DEVICE_MANUAL_OVERRIDE: self.remote_device_manual_override,
            EXPERIMENT.OPTIONS: asdict(self.execution_options),
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load Experiment Options from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """
        input_loops = dictionary[EXPERIMENT.LOOPS]
        loops = [Loop(**loop) for loop in input_loops] if input_loops is not None else None

        return ExperimentOptions(
            loops=loops,
            settings=ExperimentSettings(**dictionary[RUNCARD.SETTINGS]),
            connection=dictionary[EXPERIMENT.CONNECTION],
            device_id=dictionary[EXPERIMENT.DEVICE_ID],
            name=dictionary[RUNCARD.NAME],
            plot_y_label=dictionary[EXPERIMENT.PLOT_Y_LABEL],
            remote_device_manual_override=dictionary[EXPERIMENT.REMOTE_DEVICE_MANUAL_OVERRIDE],
            execution_options=ExecutionOptions(**dictionary[EXPERIMENT.OPTIONS]),
        )
