""" Experiment class."""
from qibo.models.circuit import Circuit

from qililab.config import __version__
from qililab.constants import EXPERIMENT, RUNCARD
from qililab.execution import EXECUTION_BUILDER
from qililab.experiment import Experiment
from qililab.platform.platform import Platform
from qililab.pulse import CircuitToPulses, PulseSchedule
from qililab.result.results import Results
from qililab.settings import RuncardSchema
from qililab.typings.experiment import ExperimentOptions
from qililab.utils.live_plot import LivePlot


class CircuitExperiment(Experiment):
    """Experiment class"""

    def __init__(
        self,
        platform: Platform,
        circuits: list[Circuit] | None = None,
        pulse_schedules: list[PulseSchedule] | None = None,
        options: ExperimentOptions = ExperimentOptions(),
    ):
        self.circuits = circuits or []
        self.pulse_schedules = pulse_schedules or []
        super().__init__(platform=platform, options=options)

    def build_execution(self):
        """Translates the list of circuits to pulse sequences (if needed) and creates the ``ExecutionManager`` class."""
        # Translate circuits into pulses if needed
        if self.circuits:
            translator = CircuitToPulses(settings=self.platform.settings)
            self.pulse_schedules = translator.translate(circuits=self.circuits, chip=self.platform.chip)
        # Build ``ExecutionManager`` class
        self.execution_manager = EXECUTION_BUILDER.build(platform=self.platform, pulse_schedules=self.pulse_schedules)

    def run(self) -> Results:
        """This method is responsible for:
        * Creating the live plotting (if connection is provided).
        * Preparing the `Results` class and the `results.yml` file.
        * Looping over all the given circuits, loops and/or software averages. And for each loop:
            * Generating and uploading the program corresponding to the circuit.
            * Executing the circuit.
            * Saving the results to the ``results.yml`` file.
            * Sending the data to the live plotting (if asked to).
            * Save the results to the ``results`` attribute.
            * Save the results to the remote database (if asked to).
        """
        # Generate live plotting
        if self.platform.connection is None:
            self._plot = None
        else:
            self._plot = LivePlot(
                connection=self.platform.connection,
                loops=self.options.loops or [],
                num_schedules=len(self.pulse_schedules),
                title=self.options.name,
            )

        return self._run()

    def compile(self) -> list[dict]:
        """Returns a dictionary containing the compiled programs of each bus for each circuit / pulse schedule of the
        experiment.

        Returns:
            list[dict]: List of dictionaries, where each dictionary has a bus alias as keys and a list of
                compiled sequences as values.
        """
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before compilation.")
        return [
            self.execution_manager.compile(schedule_idx, self.hardware_average, self.repetition_duration)
            for schedule_idx in range(len(self.pulse_schedules))
        ]

    def draw(self, resolution: float = 1.0, idx: int = 0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before drawing the experiment.")
        return self.execution_manager.draw(resolution=resolution, idx=idx)

    def to_dict(self):
        """Convert Experiment into a dictionary.

        Returns:
            dict: Dictionary representation of the Experiment class.
        """
        exp_dict = super().to_dict()
        exp_dict[EXPERIMENT.CIRCUITS] = [circuit.to_qasm() for circuit in self.circuits]
        exp_dict[EXPERIMENT.PULSE_SCHEDULES] = [pulse_schedule.to_dict() for pulse_schedule in self.pulse_schedules]
        return exp_dict

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """

        platform = Platform(runcard_schema=RuncardSchema(**dictionary[RUNCARD.PLATFORM]))
        circuits = (
            [Circuit.from_qasm(settings) for settings in dictionary[EXPERIMENT.CIRCUITS]]
            if EXPERIMENT.CIRCUITS in dictionary
            else []
        )
        pulse_schedules = (
            [PulseSchedule.from_dict(settings) for settings in dictionary[EXPERIMENT.PULSE_SCHEDULES]]
            if EXPERIMENT.PULSE_SCHEDULES in dictionary
            else []
        )
        experiment_options = ExperimentOptions.from_dict(dictionary[EXPERIMENT.OPTIONS])
        return CircuitExperiment(
            platform=platform,
            circuits=circuits,
            pulse_schedules=pulse_schedules,
            options=experiment_options,
        )

    def __str__(self):
        """String representation of an experiment."""
        exp_str = super().__str__()
        exp_str = f"{exp_str}\n{str(self.circuits)}\n{str(self.pulse_schedules)}\n"
        return exp_str
