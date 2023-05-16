"""Simulated SystemControl class."""
from dataclasses import dataclass
from enum import Enum

import numpy as np
from qilisimulator.evolution import Evolution
from qilisimulator.typings.enums import DrivingHamiltonianName, QubitName

from qililab.constants import RUNCARD
from qililab.pulse import PulseBusSchedule
from qililab.result.simulator_result import SimulatorResult
from qililab.settings import DDBBElement
from qililab.typings.enums import SystemControlName
from qililab.utils import Factory


@Factory.register
class SimulatedSystemControl:
    """SimulatedSystemControl class."""

    name: Enum = SystemControlName.SIMULATED_SYSTEM_CONTROL

    @dataclass
    class SimulatedSystemControlSettings(DDBBElement):
        """SimulatedSystemControlSettings class.

        Args:
            - qubit (string): qubit name, must refer to a valid qubit type
            - qubit_params (dict): parameters for the qubit
            - drive (string): driving hamiltonian name, must refer to a valid driving hamiltonian type
            - drive_params (dict): parameters for the driving hamiltonian
            - resolution (float): time resolution for the sampling of pulses, in ns
            - store_states (bool): indicates whether to store all states (True)
                or only those at the end of each pulse (False)

        Attributes:
            - qubit (QubitName): qubit type
            - qubit_params (dict): parameters for the qubit
            - drive (DrivingHamiltonianName): driving hamiltonian type
            - drive_params (dict)): parameters for the driving hamiltonian
            - resolution (float): time resolution for the sampling of pulses, in ns
            - store_states (bool): indicates whether to store all states (True)
                or only those at the end of each pulse (False)
        """

        qubit: QubitName
        qubit_params: dict
        drive: DrivingHamiltonianName
        drive_params: dict
        resolution: float
        store_states: bool

    settings: SimulatedSystemControlSettings
    _evo: Evolution

    def __init__(self, settings: dict):
        self.sequence: list[np.ndarray] | None = None
        self.settings = self.SimulatedSystemControlSettings(**settings)
        self._evo = Evolution(
            qubit_name=self.settings.qubit,
            qubit_params=self.settings.qubit_params,
            port_name=self.settings.drive,
            port_params=self.settings.drive_params,
            store_states=self.settings.store_states,
        )

    def __str__(self):
        """String representation of a Simulated SystemControl class."""
        return "--"

    def run(self) -> None:
        """Run the program"""
        self._evo.set_pulse_sequence(pulse_sequence=self.sequence, resolution=self.settings.resolution * 1e-9)
        self._evo.evolve()

    def acquire_result(self) -> SimulatorResult:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """
        return SimulatorResult(psi0=self._evo.psi0, states=self._evo.states, times=self._evo.times)

    def to_dict(self):
        """Return a dict representation of a SystemControl class."""
        return {
            RUNCARD.ID: self.settings.id_,
            RUNCARD.NAME: self.name.value,
            RUNCARD.CATEGORY: self.settings.category.value,
        }

    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int | None = None, repetition_duration: int | None = None
    ) -> list:
        """Compiles the ``PulseBusSchedule``.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition

        Returns:
            list: empty list
        """
        # TODO: get pulses -> check
        waveforms = pulse_bus_schedule.waveforms(resolution=self.settings.resolution)
        i_waveform = np.array(waveforms.i)
        self.sequence = [i_waveform]
        return []

    def upload(self):
        pass
