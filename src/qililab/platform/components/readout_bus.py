"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, Attenuator, Digitiser, LocalOscillator
from qililab.platform.components.bus_factory import BusFactory
from qililab.platform.components.interfaces import BusInterface
from qililab.result.qblox_results.qblox_result import QbloxResult


@BusFactory.register
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
        super().__init__(qubit=qubit, awg=awg)
        self._digitiser = digitiser
        self.instruments["digitiser"] = self._digitiser
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator

    def __str__(self):
        """String representation of a ReadoutBus."""
        return "ReadoutBus"

    def __eq__(self, other: object) -> bool:
        """compare two ReadoutBus objects"""
        return str(self) == str(other) if isinstance(other, ReadoutBus) else False

    def acquire_results(self) -> QbloxResult:
        """Acquires results through the Digitiser Instrument.

        Returns:
            results (QbloxResult): acquisitions of results
        """
        return self._digitiser.get_results()
