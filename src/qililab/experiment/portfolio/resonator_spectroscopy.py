"""This file contains a pre-defined version of a resonator spectroscopy experiment."""
from qibo.gates import M
from qibo.models import Circuit
from qiboconnection.api import API

from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, LoopOptions, Parameter
from qililab.utils import Loop


class ResonatorSpectroscopy:
    """Class used to run a resonator spectroscopy experiment on the bus with the given alias."""

    def __init__(self, platform: Platform, bus_alias: str, connection: API | None = None, device_id=9):
        # TODO: Should we make a copy of the platform to avoid changing parameters of other experiments?
        self.platform = platform
        self.bus_alias = bus_alias
        self.connection = connection
        self.device_id = device_id
        # Define circuit used in this experiment
        self.circuit = Circuit(1)
        self.circuit.add(M(0))

    def connect(self):
        """Connect to the platform instruments."""
        self.platform.connect(connections=self.connection, device_id=self.device_id)

    def initial_setup(self):
        """Configure each instrument with the values defined in the runcard."""
        self.platform.set_initial_setup()

    def bus_setup(self, parameters: dict) -> None:
        """Method used to change parameters of the bus used in the experiment. Some possible bus parameters are:

            * Parameter.GAIN_PATH0
            * Parameter.GAIN_PATH1
            * Parameter.IF
            * Parameter.INTEGRATION_LENGTH
            * Parameter.SCOPE_STORE_ENABLED

        Args:
            parameters (dict): dictionary containing parameter names as keys and parameter values as values

        Raises:
            ValueError: if a given parameter could not be set
        """
        bus = self.platform.get_bus_by_alias(self.bus_alias)

        for parameter, value in parameters.items():
            bus.set_parameter(parameter=parameter, value=value)

    def measurement_setup(self, parameters: dict) -> None:
        """Method used to change parameters of the measurement gate used in the experiment. Some possible gate
        parameters are:

            * Parameter.AMPLITUDE
            * Parameter.DURATION
            * Parameter.PHASE

        Args:
            parameters (dict): dictionary containing parameter names as keys and parameter values as values

        Raises:
            ValueError: if a given parameter could not be set
        """
        for parameter, value in parameters.items():
            self.platform.set_parameter(alias="M", parameter=parameter, value=value)

    def generate_program_and_upload(self) -> None:
        """This method generates the assembly program of the experiment and uploads it into the corresponding
        instruments."""

    def execute(self, loop_options: LoopOptions, repetition_duration=10000, hardware_average=10000):
        # Define loop
        frequency_loop = Loop(alias=self.bus_alias, parameter=Parameter.LO_FREQUENCY, options=loop_options)

        experiment_options = ExperimentOptions(
            name="Resonator Spectroscopy",
            loops=[frequency_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
            plot_y_label="Integrated Voltage (mV)",
            connection=self.connection,
        )

        experiment = Experiment(platform=self.platform, circuits=[self.circuit], options=experiment_options)
        results = experiment.execute()
