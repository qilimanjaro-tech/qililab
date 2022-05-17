"""HardwareExperiment class."""
from dataclasses import asdict, dataclass
from typing import List, Tuple

import numpy as np
from qibo.abstractions.gates import Gate
from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, I, M, X, Y
from qiboconnection.api import API

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.pulse import Pulse, PulseSequence, ReadoutPulse
from qililab.pulse.pulse_shape import Drag
from qililab.result import QbloxResult
from qililab.typings import Category
from qililab.utils import nested_dataclass


class Experiment:
    """HardwareExperiment class"""

    @nested_dataclass
    class ExperimentSettings:
        """Experiment settings."""

        @dataclass
        class ReadoutPulseSettings:
            """ReadoutPulseSettings class."""

            amplitude: float = 0.4
            duration: int = 2000
            phase: float = 0

        readout_pulse: ReadoutPulseSettings = ReadoutPulseSettings()
        hardware_average: int = 1000
        software_average: int = 1
        loop_duration: int = 10000
        delay_between_pulses: int = 50
        gate_duration: int = 100
        num_sigmas: float = 4
        drag_coefficient: float = 0

    platform: Platform
    execution: Execution
    settings: ExperimentSettings
    sequences: List[PulseSequence]
    _loop_parameters: List[Tuple[str, int, str, List[float]]]

    def __init__(
        self,
        sequences: List[Circuit | PulseSequence] | Circuit | PulseSequence,
        platform_name: str = DEFAULT_PLATFORM_NAME,
        settings: ExperimentSettings = None,
    ):
        if not isinstance(sequences, list):
            sequences = [sequences]
        self._loop_parameters = []
        self.settings = self.ExperimentSettings() if settings is None else settings
        self.platform = PLATFORM_MANAGER_DB.build(platform_name=platform_name)
        self._build_execution(sequence_list=sequences)

    def execute(self, connection: API | None = None):
        """Run execution."""
        self._start_instruments()
        plot_id = self._create_live_plot(connection=connection)
        results = (
            self._execute_loop(connection=connection, plot_id=plot_id)
            if self._loop_parameters
            else [self.execution.run(nshots=self.hardware_average, loop_duration=self.loop_duration)]
        )

        self.execution.close()
        return results

    def _execute_loop(self, connection: API | None, plot_id: str | None):
        """Loop and execute sequence over given Platform parameters.

        Args:
            plot_id (str): Plot ID.

        Returns:
            List[List[QbloxResult]]: List containing the results for each loop execution.
        """
        results: List[List[QbloxResult]] = []
        for category, id_, parameter, loop_range in self._loop_parameters:
            element, _ = self.platform.get_element(category=Category(category), id_=id_)
            for value in loop_range:
                logger.info("%s: %f", parameter, value)
                element.set_parameter(name=parameter, value=value)
                self.execution.setup()
                result = self.execution.run(nshots=self.hardware_average, loop_duration=self.loop_duration)
                results.append(result)
                self._send_plot_points(
                    connection=connection, plot_id=plot_id, x_value=value, y_value=result[0].voltages()[0]
                )
        return results

    def _start_instruments(self):
        """Connect, setup and start instruments."""
        self.execution.connect()
        self.execution.setup()
        self.execution.start()

    @property
    def parameters(self):
        """Configurable parameters of the platform.

        Returns:
            str: JSON of the platform.
        """
        return str(self.platform)

    def add_parameter_to_loop(self, category: str, id_: int, parameter: str, start: float, stop: float, num: int):
        """Add parameter to loop over during an experiment.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
        """
        loop_range = list(np.linspace(start, stop, num))
        self._loop_parameters.append((category, id_, parameter, loop_range))

    def draw(self, resolution: float = 1.0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(
            loop_duration=self.loop_duration, resolution=resolution, num_qubits=self.platform.num_qubits
        )

    def from_circuit(self, circuit: Circuit):
        """Translate a Qibo Circuit into a PulseSequence object.

        Args:
            circuit (Circuit): Qibo Circuit object.
        """
        sequence = PulseSequence(delay_between_pulses=self.delay_between_pulses)
        gates = list(circuit.queue)
        gates.append(circuit.measurement_gate)
        for gate in gates:
            if isinstance(gate, M):
                for qubit_id in gate.target_qubits:
                    sequence.add(
                        ReadoutPulse(
                            amplitude=self.readout_pulse.amplitude,
                            phase=self.readout_pulse.phase,
                            duration=self.readout_pulse.duration,
                            qubit_ids=[qubit_id],
                        )
                    )
            else:
                sequence.add(self._gate_to_pulse(gate=gate))
        return sequence

    def _gate_to_pulse(self, gate: Gate):
        """Translate gate int pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        if isinstance(gate, I):
            amplitude = 0.0
            phase = 0.0
        elif isinstance(gate, X):
            amplitude = 1
            phase = 0.0
        elif isinstance(gate, Y):
            amplitude = 1
            phase = np.pi / 2
        elif isinstance(gate, RX):
            theta = gate.parameters
            theta = (theta) % (2 * np.pi)
            if theta > np.pi:
                theta -= 2 * np.pi
            amplitude = np.abs(theta) / np.pi
            phase = 0 if theta > 0 else np.pi
        elif isinstance(gate, RY):
            theta = gate.parameters
            theta = (theta) % (2 * np.pi)
            if theta > np.pi:
                theta -= 2 * np.pi
            amplitude = np.abs(theta) / np.pi
            phase = np.pi / 2 if theta > 0 else 3 * np.pi / 4
        else:
            raise ValueError(f"Qililab has not defined a gate {gate.__class__.__name__}")
        return Pulse(
            amplitude=amplitude,
            phase=phase,
            duration=self.gate_duration,
            qubit_ids=list(gate.target_qubits),
            pulse_shape=Drag(num_sigmas=self.num_sigmas, beta=self.drag_coefficient),
        )

    def _build_execution(self, sequence_list: List[Circuit | PulseSequence]):
        """Build Execution class.

        Args:
            sequence (Circuit | PulseSequence): Sequence of gates/pulses.
        """
        self.sequences = []
        for sequence in sequence_list:
            if isinstance(sequence, Circuit):
                sequence = self.from_circuit(circuit=sequence)
            self.sequences.append(sequence)
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequences=self.sequences)

    def _create_live_plot(self, connection: API | None):
        """Create live plot."""
        if connection is not None:
            # TODO: Create plot for each different BusReadout
            return connection.create_liveplot(plot_type="LINES")

    def _send_plot_points(self, connection: API | None, plot_id: str | None, x_value: float, y_value: float):
        """Send plot points to live plot viewer.

        Args:
            plot_id (str | None): Plot ID.
            x_value (float): X value.
            y_value (float): Y value.
        """
        if plot_id and connection:
            # TODO: Plot voltages of every BusReadout in the platform
            connection.send_plot_points(plot_id=plot_id, x=x_value, y=y_value)

    @property
    def delay_between_pulses(self):
        """Experiment 'delay_between_pulses' property.

        Returns:
            int: settings.delay_between_pulses.
        """
        return self.settings.delay_between_pulses

    @property
    def num_sigmas(self):
        """Experiment 'num_sigmas' property.

        Returns:
            float: settings.num_sigmas.
        """
        return self.settings.num_sigmas

    @property
    def drag_coefficient(self):
        """Experiment 'drag_coefficient' property.

        Returns:
            float: settings.drag_coefficient.
        """
        return self.settings.drag_coefficient

    @property
    def gate_duration(self):
        """Experiment 'drag_duration' property.

        Returns:
            int: settings.gate_duration.
        """
        return self.settings.gate_duration

    @property
    def readout_pulse(self):
        """Experiment 'readout_pulse' property.

        Returns:
            ReadoutPulseSettings: settings.readout_pulse.
        """
        return self.settings.readout_pulse

    @property
    def hardware_average(self):
        """Experiment 'hardware_average' property.

        Returns:
            int: settings.hardware_average.
        """
        return self.settings.hardware_average

    @property
    def loop_duration(self):
        """Experiment 'loop_duration' property.

        Returns:
            int: settings.loop_duration.
        """
        return self.settings.loop_duration

    def to_dict(self):
        """Convert Experiment into a dictionary."""
        return {
            "settings": asdict(self.settings),
            "platform_name": self.platform.name,
            "sequence": [sequence.to_dict() for sequence in self.sequences],
            "parameters": self._loop_parameters,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """
        settings = cls.ExperimentSettings(**dictionary["settings"])
        platform_name = dictionary["platform_name"]
        sequences = [PulseSequence.from_dict(settings) for settings in dictionary["sequence"]]
        parameters = dictionary["parameters"]
        experiment = Experiment(sequences=sequences, platform_name=platform_name, settings=settings)
        experiment._loop_parameters = parameters
        return experiment

    def __del__(self):
        """Destructor."""
        self.execution.close()
