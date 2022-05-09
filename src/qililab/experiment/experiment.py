"""HardwareExperiment class."""
from dataclasses import asdict, dataclass
from typing import List, Tuple

import numpy as np
from qibo.abstractions.gates import Gate
from qibo.gates import I, X, Y

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.pulse import Pulse, PulseSequence
from qililab.pulse.pulse_shape import Drag
from qililab.typings import Category, Circuit


class Experiment:
    """HardwareExperiment class"""

    @dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 4096
        software_average: int = 10
        repetition_duration: int = 20000
        delay_between_pulses: int = 0
        gate_duration: int = 60
        num_sigmas: float = 4
        drag_coefficient: float = 0.3

    platform: Platform
    execution: Execution
    settings: ExperimentSettings
    _parameter_dicts: List[Tuple[Category, int, str, float, float, float]] = []

    def __init__(
        self, sequence: Circuit | PulseSequence, platform_name: str = DEFAULT_PLATFORM_NAME, settings: dict = None
    ):
        self.settings = self.ExperimentSettings() if settings is None else self.ExperimentSettings(**settings)
        self.platform = PLATFORM_MANAGER_DB.build(
            platform_name=platform_name, experiment_settings=asdict(self.settings)
        )
        if isinstance(sequence, Circuit):
            sequence = self.from_circuit(circuit=sequence)
        sequence.delay_between_pulses = self.delay_between_pulses
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequence=sequence)

    def execute(self):
        """Run execution."""
        results = []
        for element, parameter, start, stop, step in self._parameters_to_change:
            for value in range(start, stop, step):
                element.set_parameter(name=parameter, value=value)
                results.append(self.execution.execute())
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
        for category, id_, parameter, start, stop, step in self._parameter_dicts:
            element, _ = self.platform.get_element(category=category, id_=id_)
            yield element, parameter, start, stop, step

    def add_parameter_to_loop(self, category: str, id_: int, parameter: str, start: float, stop: float, step: float):
        """Add parameter to loop over during an experiment.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
        """
        self._parameter_dicts.append((Category(category), id_, parameter, start, stop, step))

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
        for gate in circuit.queue:
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
            amplitude = 1.0
            phase = 0.0
        elif isinstance(gate, Y):
            amplitude = 1.0
            phase = np.pi / 2
        return Pulse(
            amplitude=amplitude,
            phase=phase,
            duration=self.gate_duration,
            qubit_ids=gate.target_qubits,
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
