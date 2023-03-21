""" Experiment Options Typings """

from dataclasses import asdict, dataclass, field
from typing import List

from qiboconnection.api import API

from qililab.constants import EXPERIMENT, RUNCARD
from qililab.typings.yaml_type import yaml
from qililab.utils.loop import Loop

DEFAULT_EXPERIMENT_NAME = "experiment"


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
    name: str = DEFAULT_EXPERIMENT_NAME
    plot_y_label: str | None = None
    remote_device_manual_override: bool = field(default=False)
    remote_save: bool = True
    description: str = ""

    def __post_init__(self):
        """Raise an error if a list of hardware loops is provided."""
        # Lists of software and hardware loops. If the lists are empty, the value is set to None
        if self.loops is not None:
            self.sw_loops = [loop.sw_loop for loop in self.loops if loop.sw_loop is not None] or None
            hw_loop = [loop.hw_loop for loop in self.loops if loop.hw_loop is not None]
            if not hw_loop:  # list is empty
                self.hw_loop = None
            elif len(hw_loop) == 1:
                self.hw_loop = hw_loop[0]
            else:
                raise ValueError("Running multiple hardware loops in parallel is not supported.")
        else:
            self.sw_loops = None
            self.hw_loop = None

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
            EXPERIMENT.REMOTE_SAVE: self.remote_save,
            EXPERIMENT.DESCRIPTION: self.description,
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
            settings=ExperimentSettings(**dictionary[RUNCARD.SETTINGS])
            if RUNCARD.SETTINGS in dictionary
            else ExperimentSettings(),
            connection=dictionary.get(EXPERIMENT.CONNECTION, None),
            device_id=dictionary.get(EXPERIMENT.DEVICE_ID, None),
            name=dictionary[RUNCARD.NAME] if RUNCARD.NAME in dictionary else DEFAULT_EXPERIMENT_NAME,
            plot_y_label=dictionary.get(EXPERIMENT.PLOT_Y_LABEL, None),
            remote_device_manual_override=dictionary.get(EXPERIMENT.REMOTE_DEVICE_MANUAL_OVERRIDE, False),
            remote_save=dictionary.get(EXPERIMENT.REMOTE_SAVE, True),
            description=dictionary.get(EXPERIMENT.DESCRIPTION, ""),
        )
