"""SimulatedSystemControl class."""
from dataclasses import dataclass
from pathlib import Path
from typing import Type

import numpy as np
import qutip
from qilisimulator.constants import HBAR
from qilisimulator.driving_hamiltonian import DrivingHamiltonian
from qilisimulator.qubits.csfq4jj import (
    CSFQ4JJ,  # TODO: Change the CSFQ4JJ import to the general Qubit class
)
from qilisimulator.utils import Factory as SimulatorFactory

from qililab.instruments import Instruments
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.result import SimulatorResult
from qililab.typings import BusElementName
from qililab.utils import Factory


@Factory.register
class SimulatedSystemControl(SystemControl):
    """SimulatedSystemControl class."""

    name = BusElementName.SIMULATED_SYSTEM_CONTROL
    energy_norm: float = HBAR * 2 * np.pi

    @dataclass
    class SimulatedSystemControlSettings(SystemControl.SystemControlSettings):
        """SimulatedSystemControlSettings class."""

        qubit: CSFQ4JJ
        driving_hamiltonian: Type[DrivingHamiltonian]
        resolution: float
        frequency: float
        nsteps: int
        store_states: bool
        dimension: int

        def __post_init__(self):
            """Cast qubit to its corresponding class."""
            super().__post_init__()
            self.qubit = SimulatorFactory.get(self.qubit)()
            self.driving_hamiltonian = SimulatorFactory.get(self.driving_hamiltonian)

    settings: SimulatedSystemControlSettings
    options: qutip.Options

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        self.options = qutip.Options()

    def turn_on(self):
        """Start instrument."""

    def setup(self):
        """Setup instruments."""
        self.options = qutip.Options(nsteps=self.nsteps, store_states=self.store_states)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run the given pulse sequence."""
        waveforms = pulse_sequence.waveforms(frequency=self.frequency, resolution=self.resolution)
        i_waveform = np.array(waveforms.i) * self.amplitude_norm_factor
        hamiltonian = self.hamiltonian(
            qubit=self.qubit,
            waveforms=i_waveform,
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

    @property
    def delay_time(self):
        """SystemControl 'delay_time' property. Delay (in ns) between the readout pulse and the acquisition."""
        raise AttributeError("SimulatedSystemControl class doesn't have a 'delay_time' property.")
