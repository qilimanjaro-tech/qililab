"""HardwareExperiment class."""
from dataclasses import asdict, dataclass
from typing import List, Tuple

import numpy as np
from qibo.abstractions.gates import Gate
from qibo.core.circuit import Circuit
from qibo.gates import I, M, X, Y
from qiboconnection.api import API

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import (
    PLATFORM_MANAGER_DB,
    PLATFORM_MANAGER_YAML,
    Platform,
    PlatformSchema,
)
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
        repetition_duration: int = 2000
        delay_between_pulses: int = 0
        gate_duration: int = 100
        num_sigmas: float = 4
        drag_coefficient: float = 0.3

    platform: Platform
    execution: Execution
    settings: ExperimentSettings
    sequence: PulseSequence
    _parameter_dicts: List[Tuple[Category, int, str, float, float, float]] = []

    def __init__(
        self,
        sequence: Circuit | PulseSequence,
        platform_name: str = DEFAULT_PLATFORM_NAME,
        settings: ExperimentSettings = None,
        connection: API | None = None,
    ):
        self.connection = connection
        self.settings = self.ExperimentSettings() if settings is None else settings
        self.platform = PLATFORM_MANAGER_DB.build(
            platform_name=platform_name, experiment_settings=asdict(self.settings)
        )
        if isinstance(sequence, Circuit):
            sequence = self.from_circuit(circuit=sequence)
        sequence.delay_between_pulses = self.delay_between_pulses
        self.sequence = sequence
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequence=sequence)

    def execute(self):
        """Run execution."""
        self.execution.connect()
        self.execution.setup()
        self.execution.start()
        if self.connection is not None:
            # TODO: Create plot for each different BusReadout
            plot_id = self.connection.create_liveplot(plot_type="LINES")
        results: List[List[QbloxResult]] = []
        for element, parameter, start, stop, num in self._parameters_to_change:
            for value in np.linspace(start, stop, num):
                print(f"{parameter}: {value}")
                element.set_parameter(name=parameter, value=value)
                self.execution.setup()
                result = self.execution.run()
                results.append(result)
                if self.connection is not None:
                    # TODO: Plot voltages of every BusReadout in the platform
                    self.connection.send_plot_points(plot_id=plot_id, x=value, y=result[0].voltages()[0])
        self.execution.close()
        return results

    @property
    def parameters(self):
        """Configurable parameters of the platform.

        Returns:
            str: JSON of the platform.
        """
        return str(self.platform)

    @property
    def _parameters_to_change(self):
        """Generator returning the information of the parameters to loop over."""
        for category, id_, parameter, start, stop, num in self._parameter_dicts:
            element, _ = self.platform.get_element(category=category, id_=id_)
            yield element, parameter, start, stop, num

    def add_parameter_to_loop(self, category: str, id_: int, parameter: str, start: float, stop: float, num: int):
        """Add parameter to loop over during an experiment.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
        """
        self._parameter_dicts.append((Category(category), id_, parameter, start, stop, num))

    def draw(self, resolution: float = 1.0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution)

    def from_circuit(self, circuit: Circuit):
        """Translate a Qibo Circuit into a PulseSequence object.

        Args:
            circuit (Circuit): Qibo Circuit object.
        """
        sequence = PulseSequence()
        gates = list(circuit.queue)
        gates.append(circuit.measurement_gate)
        for gate in gates:
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
        elif isinstance(gate, M):
            return ReadoutPulse(
                amplitude=self.readout_pulse.amplitude,
                phase=self.readout_pulse.phase,
                duration=self.readout_pulse.duration,
                qubit_ids=list(gate.target_qubits),
            )
        else:
            raise ValueError(f"Qililab has not defined a gate {type(gate).__class__}")
        return Pulse(
            amplitude=amplitude,
            phase=phase,
            duration=self.gate_duration,
            qubit_ids=list(gate.target_qubits),
            pulse_shape=Drag(num_sigmas=self.num_sigmas, beta=self.drag_coefficient),
        )

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

    def to_dict(self):
        """Convert Experiment into a dictionary."""
        return {
            "settings": asdict(self.settings),
            "platform_name": self.platform.name,
            "sequence": self.sequence.to_dict(),
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """
        settings = cls.ExperimentSettings(**dictionary["settings"])
        platform_name = dictionary["platform_name"]
        sequence = PulseSequence.from_dict(dictionary["sequence"])
        return Experiment(sequence=sequence, platform_name=platform_name, settings=settings)
