"""Simulated SystemControl class."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from qilisimulator.evolution import Evolution
from qilisimulator.typings.enums import DrivingHamiltonianName, QubitName

from qililab.constants import RUNCARD
from qililab.pulse import PulseBusSchedule
from qililab.result.simulator_result import SimulatorResult
from qililab.system_controls.system_control import SystemControl
from qililab.typings import SystemControlCategory
from qililab.typings.enums import Category, Parameter, SystemControlName, SystemControlSubCategory
from qililab.utils.factory import Factory


@Factory.register
class SimulatedSystemControl(SystemControl):
    """SimulatedSystemControl class."""

    name = SystemControlName.SIMULATED_SYSTEM_CONTROL

    @dataclass
    class SimulatedSystemControlSettings(SystemControl.SystemControlSettings):
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

        system_control_category = SystemControlCategory.SIMULATED
        system_control_subcategory = SystemControlSubCategory.SIMULATED
        # Note: DDBBElement already casts enums from value
        qubit: QubitName
        qubit_params: dict
        drive: DrivingHamiltonianName
        drive_params: dict
        resolution: float
        store_states: bool

    settings: SimulatedSystemControlSettings
    _evo: Evolution

    def __init__(self, settings: dict):
        super().__init__(settings=settings, instruments=None)
        self._evo = Evolution(
            qubit_name=self.settings.qubit,
            qubit_params=self.settings.qubit_params,
            port_name=self.settings.drive,
            port_params=self.settings.drive_params,
            store_states=self.settings.store_states,
        )

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return []

    def __str__(self):
        """String representation of a Simulated SystemControl class."""
        return "--"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set parameter for an instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """

    def generate_program(self, pulse_bus_schedule: PulseBusSchedule):
        """Translate a Pulse Bus Schedule to a simulated program

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            frequency (float | None): frequency to modulate the pulses. Optional
        """
        resolution = self.settings.resolution
        # TODO: get pulses -> check
        waveforms = pulse_bus_schedule.waveforms(resolution=resolution)
        i_waveform = np.array(waveforms.i)
        sequence = [i_waveform]

        # Init evolution pulse sequence
        self._evo.set_pulse_sequence(pulse_sequence=sequence, resolution=resolution * 1e-9)

    def run(self) -> None:
        """Run the program"""
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
            RUNCARD.ID: self.id_,
            RUNCARD.NAME: self.name.value,
            RUNCARD.CATEGORY: self.settings.category.value,
            RUNCARD.SYSTEM_CONTROL_CATEGORY: self.settings.system_control_category.value,
            RUNCARD.SYSTEM_CONTROL_SUBCATEGORY: self.settings.system_control_subcategory.value,
        }

    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
        """

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        return 0
