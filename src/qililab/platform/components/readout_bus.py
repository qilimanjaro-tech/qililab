"""Driver for the Drive Bus class."""
from typing import Any

from qililab.drivers.interfaces import AWG, Attenuator, Digitiser, LocalOscillator
from qililab.platform.components.interfaces import BusInterface
from qililab.pulse import PulseBusSchedule
from qililab.result.qblox_results.qblox_result import QbloxResult


class ReadoutBus(BusInterface):
    """Qililab's driver for Readout Bus"""

    def __init__(
        self,
        qubit: int,
        awg: AWG,
        digitiser: Digitiser,
        local_oscillator: LocalOscillator | None,
        attenuator: Attenuator | None,
    ):
        """Initialise the bus.

        Args:
            qubit (int): Qubit
            awg (AWG): Arbitrary Wave Generator instance
            digitiser (Digitiser): Arbitrary Wave Generator instance to acquire results
            local_oscillator (LocalOscillator): Local Oscillator
            attenuator (Attenuator): Attenuator
        """
        super().__init__()
        self.qubit = qubit
        self.awg = awg
        self.digitiser = digitiser
        if local_oscillator:
            self.local_oscillator = local_oscillator
        if attenuator:
            self.attenuator = attenuator

    def execute(
        self,
        instrument_name: str,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        num_bins: int,
    ) -> None:
        """Execute a pulse bus schedule through an AWG or Digitiser Instrument belonging to the bus.
           Because Digitiser inherits from AWG, we only need to check for AWG instances, which is the interface
           defining the abstract method for execution of Qprograms.

        Args:
            instrument_name (str): Name of the instrument
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """
        instrument = getattr(self, instrument_name, None)
        if isinstance(instrument, AWG):
            instrument.execute(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
                num_bins=num_bins,
            )

    def acquire_results(self) -> QbloxResult:
        """Acquires results using the digitiser of the bus.

        Returns:
            results (QbloxResult): acquisitions of results
        """
        return self.digitiser.get_results()

    def set(self, instrument_name: str, param_name: str, value: Any) -> None:
        """Set parameter on the bus' instruments.

        Args:
            instrument_name (str): Name of the instrument to set parameter on
            param (str): Parameter's name.
            value (Any): Parameter's value
        """
        if instrument := getattr(self, instrument_name, None):
            instrument.set(param_name, value)

    def get(self, instrument_name: str, param_name: str) -> Any:
        """Return value associated to a parameter on the bus' instrument.

        Args:
            instrument_name (str): Name of the instrument to get parameter from
            param (str): Parameter's name.

        Returns:
            value (Any): Parameter's value
        """
        return instrument.get(param_name) if (instrument := getattr(self, instrument_name, None)) else None
