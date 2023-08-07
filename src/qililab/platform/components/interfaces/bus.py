"""Bus Class Interface."""
from abc import ABC
from typing import Any

from qililab.drivers.interfaces import BaseInstrument
from qililab.drivers.interfaces.awg import AWG
from qililab.pulse import PulseBusSchedule, PulseDistortion


class Bus(ABC):
    """Bus Class."""

    def __init__(self, qubit: int, awg: AWG):
        """Initialise the bus.

        Args:
            qubit (int): Qubit
            awg (AWG): Sequencer
            local_oscillator (LocalOscillator | None): Local oscillator
            attenuator (Attenuator | None): Attenuator
        """
        self.qubit = qubit
        self._awg = awg
        self.instruments: dict[str, BaseInstrument] = {"awg": self._awg}
        self.delay = 0
        self.distortions: list[PulseDistortion] = []

    def execute(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        num_bins: int,
    ) -> None:
        """Execute a pulse bus schedule through the AWG Instrument.

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
            AttributeError: if more than one instrument has the same parameter name.
            AttributeError: if no instrument is found for the parameter name.
        """
        if param_name == "delay":
            self.delay = value
        elif param_name == "distortions":
            self.distortions = value
        else:
            candidates: list[BaseInstrument] = [
                instrument for instrument in self.instruments.values() if param_name in instrument.params
            ]
            if len(candidates) == 1:
                candidates[0].set(param_name, value)
            elif len(candidates) > 1:
                raise AttributeError("More than one instrument with the same parameter name found in the bus.")
            else:
                raise AttributeError("No instrument found in the bus for the parameter name.")

    def get(self, param_name: str) -> Any:
        """Return value associated to a parameter on the bus' instrument.

        Args:
            param (str): Parameter's name.

        Returns:
            value (Any): Parameter's value

        Raises:
            AttributeError: if more than one instrument has the same parameter name.
            AttributeError: if no instrument is found for the parameter name.
        """
        if param_name == "delay":
            return self.delay
        if param_name == "distortions":
            return self.distortions
        candidates: list[BaseInstrument] = [
            instrument for instrument in self.instruments.values() if param_name in instrument.params
        ]
        if len(candidates) == 1:
            return candidates[0].get(param_name)
        if len(candidates) > 1:
            raise AttributeError("More than one instrument with the same parameter name found in the bus.")
        raise AttributeError("No instrument found in the bus for the parameter name.")
