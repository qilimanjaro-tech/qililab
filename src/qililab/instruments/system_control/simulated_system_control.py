"""SimulatedSystemControl class."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from qilisimulator.evolution import Evolution
from qilisimulator.typings.enums import DrivingHamiltonianName, QubitName

from qililab.instruments.instruments import Instruments
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.result.simulator_result import SimulatorResult
from qililab.typings.enums import Parameter, SystemControlSubcategory
from qililab.utils.factory import Factory


@Factory.register
class SimulatedSystemControl(SystemControl):
    """SimulatedSystemControl class."""

    name = SystemControlSubcategory.SIMULATED_SYSTEM_CONTROL

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

        # Note: DDBBElement already casts enums from value
        qubit: QubitName
        qubit_params: dict
        drive: DrivingHamiltonianName
        drive_params: dict
        resolution: float
        store_states: bool

    settings: SimulatedSystemControlSettings
    _evo: Evolution

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        self._evo = Evolution(
            qubit_name=self.settings.qubit,
            qubit_params=self.settings.qubit_params,
            port_name=self.settings.drive,
            port_params=self.settings.drive_params,
            store_states=self.settings.store_states,
        )

    def start(self):
        """Start instrument."""

    def setup(self, frequencies: list[float]):
        """Setup instruments."""

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set parameter for an instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run the given pulse sequence."""

        resolution = self.settings.resolution
        frequency = self.frequency
        if pulse_sequence.frequency is not None:
            frequency = pulse_sequence.frequency

        # TODO: get pulses -> check
        waveforms = pulse_sequence.waveforms(frequency=frequency, resolution=resolution)
        i_waveform = np.array(waveforms.i)
        sequence = [i_waveform]

        # Init evolution pulse sequence
        self._evo.set_pulse_sequence(pulse_sequence=sequence, resolution=resolution * 1e-9)

        # Evolve
        self._evo.evolve()

        # Store results
        return SimulatorResult(psi0=self._evo.psi0, states=self._evo.states, times=self._evo.times)

    @property
    def awg_frequency(self):
        """SimulatedSystemControl 'awg_frequency' property.

        Returns:
            float: Normalized frequency of the applied pulses.
        """
        return 2e6  # simulator doesn't have an AWG frequency, but this is needed for the plotting of the pulses

    @property
    def frequency(self):
        """SimulatedSystemControl 'frequency' property.

        Returns:
            float: qubit frequency
        """
        return self._evo.system.qubit.frequency

    @frequency.setter
    def frequency(self, target_freqs: list[float]):
        """SimulatedSystemControl 'frequency' property setter.

        Note:
            - The property value is not actually changed.
            - This serves as a bypass for the frequency setter used for physical qubits.
        """

    @property
    def acquisition_delay_time(self):
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        raise AttributeError("SimulatedSystemControl class doesn't have a 'acquisition_delay_time' property.")
