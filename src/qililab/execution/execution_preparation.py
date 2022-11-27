"""Execution preparation class."""

from dataclasses import dataclass
from pathlib import Path

from qililab.constants import EXPERIMENT, EXPERIMENT_FILENAME, RESULTS_FILENAME
from qililab.execution.execution import Execution
from qililab.remote_connection import RemoteAPI
from qililab.result.results import Results
from qililab.typings.experiment import ExperimentOptions
from qililab.typings.yaml_type import yaml
from qililab.utils.live_plot import LivePlot
from qililab.utils.results_data_management import create_results_folder
from qililab.utils.util_loops import compute_shapes_from_loops


@dataclass
class ExecutionPreparation:
    """Create all necessary preparation for an execution"""

    remote_api: RemoteAPI
    options: ExperimentOptions

    def _create_results_file(self, num_schedules: int, path: Path):
        """Create 'results.yml' file.

        Args:
            path (Path): Path to data folder.
        """

        data = {
            EXPERIMENT.SOFTWARE_AVERAGE: self.options.settings.software_average,
            EXPERIMENT.NUM_SCHEDULES: num_schedules,
            EXPERIMENT.SHAPE: [] if self.options.loops is None else compute_shapes_from_loops(loops=self.options.loops),
            EXPERIMENT.LOOPS: [loop.to_dict() for loop in self.options.loops]
            if self.options.loops is not None
            else None,
            EXPERIMENT.RESULTS: None,
        }
        with open(file=path / RESULTS_FILENAME, mode="w", encoding="utf-8") as results_file:
            yaml.dump(data=data, stream=results_file, sort_keys=False)

    def _dump_experiment_data(self, path: Path, experiment_serialized: dict):
        """Dump experiment data.

        Args:
            path (Path): Path to data folder.
        """
        with open(file=path / EXPERIMENT_FILENAME, mode="w", encoding="utf-8") as experiment_file:
            yaml.dump(data=experiment_serialized, stream=experiment_file, sort_keys=False)

    def prepare_execution_and_load_schedule(
        self, execution: Execution, experiment_serialized: dict, schedule_index_to_load: int = 0
    ) -> tuple[LivePlot, Results, Path, bool]:
        """Prepares the experiment with the following steps:
          - Create results data files and Results object
          - Serializes the Experiment information to a file
          - Creates Live Plotting (if required)
          - uploads the specified schedule to the AWGs (if buses admit that)

        Args:
            schedule_index_to_load (int, optional): specific schedule to load. Defaults to 0.
        """
        plot, results, results_path, execution_ready = self.prepare_execution(
            num_schedules=execution.num_schedules, experiment_serialized=experiment_serialized
        )
        execution.connect_setup_and_turn_on_if_needed()
        self._load_schedule(
            execution=execution, schedule_index_to_load=schedule_index_to_load, results_path=results_path
        )
        return plot, results, results_path, execution_ready

    def prepare_execution(
        self, num_schedules: int, experiment_serialized: dict
    ) -> tuple[LivePlot, Results, Path, bool]:
        """Prepares the experiment with the following steps:
        - Create results data files and Results object
        - Serializes the Experiment information to a file
        - Creates Live Plotting (if required)
        """
        self.remote_api.block_remote_device()

        results_path = create_results_folder(name=self.options.name)
        self._create_results_file(num_schedules=num_schedules, path=results_path)
        self._dump_experiment_data(path=results_path, experiment_serialized=experiment_serialized)
        plot = LivePlot(
            remote_api=self.remote_api,
            loops=self.options.loops,
            plot_y_label=self.options.plot_y_label,
            num_schedules=num_schedules,
        )
        results = Results(
            software_average=self.options.settings.software_average,
            num_schedules=num_schedules,
            loops=self.options.loops,
        )
        execution_ready = True
        return plot, results, results_path, execution_ready

    def _load_schedule(self, execution: Execution, schedule_index_to_load: int, results_path: Path) -> None:
        """uploads the specified schedule to the AWGs (if buses admit that)

        Args:
            schedule_index_to_load (int): specific schedule to load
        """
        execution.generate_program_and_upload(
            schedule_index_to_load=schedule_index_to_load,
            nshots=self.options.settings.hardware_average,
            repetition_duration=self.options.settings.repetition_duration,
            path=results_path,
        )
