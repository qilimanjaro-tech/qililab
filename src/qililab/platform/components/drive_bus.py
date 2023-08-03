"""Driver for the Drive Bus class."""
from typing import Any

from qililab.drivers.interfaces.attenuator import Attenuator
from qililab.drivers.interfaces.awg import AWG
from qililab.drivers.interfaces.local_oscillator import LocalOscillator
from qililab.platform.components.bus_factory import BusFactory
from qililab.platform.components.interfaces import BusInterface
from qililab.pulse import PulseBusSchedule, PulseDistortion


@BusFactory.register
class DriveBus(BusInterface):
    """Qililab's driver for Drive Bus"""

    def __init__(self, qubit: int, awg: AWG, local_oscillator: LocalOscillator | None, attenuator: Attenuator | None):
        """Initialise the bus.

        Args:
            qubit (int): Qubit
            awg (AWG): Sequencer
            local_oscillator (LocalOscillator | None): Local oscillator
            attenuator (Attenuator | None): Attenuator
            distortions (list[PulseDistortion]): List of the distortions to apply to the Bus.
            delay (int): Bus delay
        """
        self.qubit = qubit
        self._awg = awg
        self.instruments: dict[str, AWG | LocalOscillator | Attenuator ] = {
            'awg': self._awg
        }
        if local_oscillator:
            self.instruments['local_oscillator'] = local_oscillator
        if attenuator:
            self.instruments['attenuator'] = attenuator
        self.delay = 0
        self.distortions: list[PulseDistortion] = []

    def execute(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        num_bins: int,
    ) -> None:
        """Execute a pulse bus schedule through an AWGs Instrument belonging to the bus.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """
        self._awg.execute(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
                num_bins=num_bins,
            )

    def set(self, param_name: str, value: Any) -> None:
        """Set parameter on the bus' instruments.

        Args:
            param (str): Parameter's name.
            value (Any): Parameter's value

        Raises:
            Exception: if more than one instrument has the same parameter name.
        """
        candidates: list[AWG | LocalOscillator | Attenuator] = []
        for instrument in self.instruments.values():
            if param_name in instrument.params:
                candidates.append(instrument)

        if len(candidates) == 1:
            return candidates[0].set(param_name, value)
        elif len(candidates) > 1:
            raise Exception("More than one instrument with the same parameter name found in the bus.")
        elif len(candidates) == 0:
            raise Exception("No instrument found in the bus for the parameter name.")

    def get(self, param_name: str) -> Any:
        """Return value associated to a parameter on the bus' instrument.

        Args:
            param (str): Parameter's name.

        Returns:
            value (Any): Parameter's value

        Raises:
            Exception: if more than one instrument has the same parameter name.
        """
        candidates: list[AWG | LocalOscillator | Attenuator] = [instrument for instrument in self.instruments.values() if param_name in instrument.params]

        if len(candidates) == 1:
            return candidates[0].get(param_name)
        elif len(candidates) > 1:
            raise Exception("More than one instrument with the same parameter name found in the bus.")
        elif len(candidates) == 0:
            raise Exception("No instrument found in the bus for the parameter name.")
