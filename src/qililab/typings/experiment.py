""" Experiment Options Typings """

from dataclasses import asdict, dataclass, field

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

    loops: list[Loop] | None = None
    settings: ExperimentSettings = field(default_factory=ExperimentSettings)
    name: str = DEFAULT_EXPERIMENT_NAME
    remote_save: bool = True
    description: str = ""

    def to_dict(self):
        """Convert Experiment into a dictionary.

        Returns:
            dict: Dictionary representation of the Experiment class.
        """
        return {
            EXPERIMENT.LOOPS: [loop.to_dict() for loop in self.loops] if self.loops is not None else None,
            RUNCARD.SETTINGS: asdict(self.settings),
            RUNCARD.NAME: self.name,
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
            name=dictionary[RUNCARD.NAME] if RUNCARD.NAME in dictionary else DEFAULT_EXPERIMENT_NAME,
            remote_save=dictionary.get(EXPERIMENT.REMOTE_SAVE, True),
            description=dictionary.get(EXPERIMENT.DESCRIPTION, ""),
        )
