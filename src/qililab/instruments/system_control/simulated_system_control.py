"""SimulatedSystemControl class."""
from typing import Type

import numpy as np
import qutip
from qilisimulator.constants import HBAR
from qilisimulator.driving_hamiltonian import DrivingHamiltonian
from qilisimulator.qubits import Qubit
from qilisimulator.utils import Factory as SimulatorFactory

from qililab.config import logger
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.result import SimulatorResult
from qililab.typings import BusElementName
from qililab.utils import Factory, nested_dataclass


@Factory.register
class SimulatedSystemControl(SystemControl):
    """SimulatedSystemControl class."""

    @nested_dataclass
    class SimulatedSystemControlSettings(SystemControl.SystemControlSettings):
        """SimulatedSystemControlSettings class."""

        qubit: Qubit
        driving_hamiltonian: Type[DrivingHamiltonian]
        resolution: float
        frequency: float
        nsteps: int
        store_states: bool
        dimension: int

        def __post_init__(self):
            """Cast qubit to its corresponding class."""
            self.qubit = SimulatorFactory.get(self.qubit)()
            self.driving_hamiltonian = SimulatorFactory.get(self.driving_hamiltonian)

    settings: SimulatedSystemControlSettings
    options: qutip.Options
    energy_norm = HBAR * 2 * np.pi

    name = BusElementName.SIMULATED_SYSTEM_CONTROL

    def __init__(self, settings: dict):
        self.settings = self.SimulatedSystemControlSettings(**settings)

    def connect(self):
        """Connect to the instruments."""

    def setup(self):
        """Setup instruments."""
        self.options = qutip.Options(nsteps=self.nsteps, store_states=self.store_states)

    def start(self):
        """Start/Turn on the instruments."""

    def run(self, pulse_sequence: PulseSequence, nshots: int, loop_duration: int):
        """Run the given pulse sequence."""
        waveforms_i, _ = pulse_sequence.waveforms(frequency=self.frequency, resolution=self.resolution)
        waveforms = np.array(waveforms_i) * self.amplitude_norm_factor
        hamiltonian = self.hamiltonian(
            qubit=self.qubit,
            waveforms=waveforms,
            dimension=self.dimension,
            energy_norm=self.energy_norm,
            resolution=self.resolution,
        )
        hami, tlist = hamiltonian.to_qutip()
        _, eigen_states = hami[0].eigenstates()
        init0 = qutip.ket2dm(eigen_states[0])
        init1 = qutip.ket2dm(eigen_states[1])
        eops = [init0, init1]
        results = qutip.mesolve(hami, init0, tlist, options=self.options, e_ops=eops)
        return SimulatorResult(prob_0=results.expect[0][-1], prob_1=results.expect[1][-1])

    def close(self):
        """Close connection to the instruments."""

    @property
    def amplitude_norm_factor(self) -> float:
        """SimulatedSystemControl 'amplitude_norm_factor' property.

        Returns:
            float: Normalization factor used for the pulse amplitude.
        """
        # TODO: Add the 0.2 in the pi_pulse_amplitude parameter of the qubit
        return np.abs(self.qubit.a_b()[0] / self.energy_norm) * 0.2

    @property
    def hamiltonian(self):
        """SimulatedSystemControl 'Hamiltonian' property.

        Returns:
            Type[DrivingHamiltonian]: Hamiltonian class type.
        """
        return self.settings.driving_hamiltonian

    @property
    def qubit(self):
        """SimulatedSystemControl 'qubit' property.

        Returns:
            Qubit: Qubit object.
        """
        return self.settings.qubit

    @property
    def nsteps(self):
        """SimulatedSystemControl 'nsteps' property.

        Returns:
            int: Qutip's number of steps.
        """
        return self.settings.nsteps

    @property
    def dimension(self):
        """SimulatedSystemControl 'dimension' property.

        Returns:
            int: Dimension of the qubit.
        """
        return self.settings.dimension

    @property
    def store_states(self):
        """SimulatedSystemControl 'store_states' property.

        Returns:
            bool: Flag to store states by Qutip.
        """
        return self.settings.store_states

    @property
    def frequency(self):
        """SimulatedSystemControl 'frequency' property.

        Returns:
            float: Normalized frequency of the applied pulses.
        """
        return self.settings.frequency

    @property
    def resolution(self):
        """SimulatedSystemControl 'resolution' property.

        Returns:
            float: Resolution of the pulse in ns.
        """
        return self.settings.resolution
