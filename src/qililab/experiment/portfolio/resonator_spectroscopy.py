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

    def execute(self, alias: str, loop_options: LoopOptions, repetition_duration=10000, hardware_average=10000):
        # Define loop
        frequency_loop = Loop(parameter=Parameter.LO_FREQUENCY, alias=alias, options=loop_options)

        experiment_options = ExperimentOptions(
            name="Resonator Spectroscopy",
            loops=[frequency_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
            plot_y_label="Integrated Voltage (mV)",
            connection=self.connection,
        )

        experiment = Experiment(platform=self.platform, circuits=[self.circuit], options=experiment_options)
        return experiment

    def setup(self):
        m_amplitude = 1.0
        m_duration = 8000
        qrm_gain = 1.0
        qrm_if_frequency = 2e7
        qrm_integration_length = 8000
        qrm_scope_store_enabled = False

        bus = self.platform.get_bus_by_alias(self.bus_alias)

        self.platform.set_parameter(alias="M", parameter=Parameter.AMPLITUDE, value=m_amplitude)
        self.platform.set_parameter(alias="M", parameter=Parameter.DURATION, value=m_duration)
        bus.set_parameter(parameter=Parameter.GAIN_PATH0, value=qrm_gain, channel_id=0)
        bus.set_parameter(parameter=Parameter.GAIN_PATH1, value=qrm_gain, channel_id=0)
        bus.set_parameter(parameter=Parameter.IF, value=qrm_if_frequency, channel_id=0)
        bus.set_parameter(parameter=Parameter.INTEGRATION_LENGTH, value=qrm_integration_length)
        bus.set_parameter(parameter=Parameter.SCOPE_STORE_ENABLED, value=qrm_scope_store_enabled, channel_id=0)
