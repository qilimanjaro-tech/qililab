# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Experiment Options Typings """
import io
from dataclasses import asdict, dataclass, field

from ruamel.yaml import YAML

from qililab.constants import EXPERIMENT, RUNCARD
from qililab.utils.loop import Loop

DEFAULT_EXPERIMENT_NAME = "experiment"


@dataclass
class ExperimentSettings:
    """Experiment settings."""

    hardware_average: int = 1024
    software_average: int = 1
    repetition_duration: int = 200000
    num_bins: int = 1

    def __str__(self):
        """Returns a string representation of the experiment settings."""
        return str(YAML().dump(asdict(self), io.BytesIO()))


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
            RUNCARD.GATES_SETTINGS: asdict(self.settings),
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
            settings=ExperimentSettings(**dictionary[RUNCARD.GATES_SETTINGS])
            if RUNCARD.GATES_SETTINGS in dictionary
            else ExperimentSettings(),
            name=dictionary[RUNCARD.NAME] if RUNCARD.NAME in dictionary else DEFAULT_EXPERIMENT_NAME,
            remote_save=dictionary.get(EXPERIMENT.REMOTE_SAVE, True),
            description=dictionary.get(EXPERIMENT.DESCRIPTION, ""),
        )
