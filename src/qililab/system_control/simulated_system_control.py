"""Simulated SystemControl class."""
from dataclasses import dataclass, field

import numpy as np
from qilisimulator.evolution import Evolution
from qilisimulator.typings.enums import DrivingHamiltonianName, QubitName

from qililab.constants import RUNCARD
from qililab.instruments import Instrument, Instruments
from qililab.pulse import PulseBusSchedule
from qililab.result.simulator_result import SimulatorResult
from qililab.typings.enums import SystemControlName
from qililab.utils.factory import Factory

from .readout_system_control import ReadoutSystemControl


@Factory.register
class SimulatedSystemControl(ReadoutSystemControl):
    """SimulatedSystemControl class."""

    name = SystemControlName.SIMULATED_SYSTEM_CONTROL

    @dataclass
    class SimulatedSystemControlSettings(ReadoutSystemControl.SystemControlSettings):
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
        instruments: list[Instrument] = field(init=False, default_factory=list)

    settings: SimulatedSystemControlSettings
    _evo: Evolution

    def __init__(self, settings: dict, platform_instruments: Instruments | None = None):
        self.sequence: list[np.ndarray] | None = None
        super().__init__(settings=settings, platform_instruments=platform_instruments)
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

    def run(self, port: str) -> None:
        """Run the program.

        Args:
            port (str): Port of the chip.
        """
        self._evo.set_pulse_sequence(pulse_sequence=self.sequence, resolution=self.settings.resolution * 1e-9)
        self._evo.evolve()

    def acquire_result(self, port: str) -> SimulatorResult:
        """Read the result from the AWG instrument
        Args:
            port (str): Port of the chip.

        Returns:
            SimulatorResult: Acquired result.
        """
        return SimulatorResult(psi0=self._evo.psi0, states=self._evo.states, times=self._evo.times)

    def to_dict(self):
        """Return a dict representation of a SystemControl class."""
        return {RUNCARD.NAME: self.name.value}

    def compile(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int | None = None,
        repetition_duration: int | None = None,
        num_bins: int = 1,
    ) -> list:
        """Compiles the ``PulseBusSchedule``.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            num_bins (int, optional): Number of bins used. Defaults to 1.

        Returns:
            list: Empty list.
        """
        # TODO: get pulses -> check
        waveforms = pulse_bus_schedule.waveforms(resolution=self.settings.resolution)
        i_waveform = np.array(waveforms.i)
        self.sequence = [i_waveform]
        return []

    def upload(self, port: str):
        """Upload sequence.

        This method is added just for compatibility with qililab's workflow.

        Args:
            port (str): Port of the chip.
        """
        pass
