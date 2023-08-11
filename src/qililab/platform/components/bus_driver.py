"""Bus Class Interface."""
from abc import ABC
from typing import Any

from qpysequence.sequence import Sequence as QpySequence

from qililab.drivers.interfaces import BaseInstrument
from qililab.drivers.interfaces.awg import AWG
from qililab.pulse import PulseBusSchedule, PulseDistortion


class BusDriver(ABC):
    """Bus Class."""

    def __init__(self, alias: str, port: int, awg: AWG | None):
        """Initialise the bus.

        Args:
            alias (str): Bus alias
            port (int): Port to target
            awg (AWG): Sequencer
            local_oscillator (LocalOscillator | None): Local oscillator
            attenuator (Attenuator | None): Attenuator
        """
        self.alias = alias
        self.port = port
        self._awg = awg
        self.instruments: dict[str, BaseInstrument | None] = {"awg": self._awg}
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
        if self._awg:
            self._awg.execute(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
                num_bins=num_bins,
            )

    def execute_qpysequence(self, qpysequence: QpySequence) -> None:
        """Execute a qpysequence through the AWG Instrument.

        Args:
            qpysequence: The qpysequence to execute.
        """
        self._awg.execute_qpysequence(qpysequence=qpysequence)

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
            raise NotImplementedError("Setting distortion parameters of a bus is not yet implemented..")
        else:
            candidates: list[BaseInstrument | None] = [
                instrument for instrument in self.instruments.values() if instrument and param_name in instrument.params
            ]
            if len(candidates) == 1 and isinstance(candidates[0], BaseInstrument):
                candidates[0].set(param_name, value)
            elif len(candidates) == 2 and candidates[0] == candidates[1] and isinstance(candidates[0], BaseInstrument):
                candidates[0].set(param_name, value)
            elif len(candidates) > 1:
                raise AttributeError(f"Bus {self.alias} contains multiple instruments with the parameter {param_name}.")
            else:
                raise AttributeError(
                    f"Bus {self.alias} doesn't contain any instrument with the parameter {param_name}."
                )

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
            raise NotImplementedError("Getting distortion parameters of a bus is not yet implemented.")
        candidates: list[BaseInstrument | None] = [
            instrument for instrument in self.instruments.values() if instrument and param_name in instrument.params
        ]
        if len(candidates) == 1 and isinstance(candidates[0], BaseInstrument):
            return candidates[0].get(param_name)
        if len(candidates) == 2 and candidates[0] == candidates[1] and isinstance(candidates[0], BaseInstrument):
            return candidates[0].get(param_name)
        if len(candidates) > 1:
            raise AttributeError(f"Bus {self.alias} contains multiple instruments with the parameter {param_name}.")
        raise AttributeError(f"Bus {self.alias} doesn't contain any instrument with the parameter {param_name}.")

    def __eq__(self, other: object) -> bool:
        """compare two Bus objects"""
        return str(self) == str(other) if isinstance(other, BusDriver) else False

    def __str__(self):
        """String representation of a Bus."""
        return (
            f"{self.alias} ({self.__class__.__name__}): "
            + "".join(f"--|{instrument.name}|" for instrument in self.instruments.values())
            + f"--> port {self.port}"
        )
