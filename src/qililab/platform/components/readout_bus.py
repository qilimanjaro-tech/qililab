"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, Attenuator, Digitiser, LocalOscillator
from qililab.platform.components import BusDriver
from qililab.platform.components.bus_factory import BusFactory
from qililab.result.qblox_results.qblox_result import QbloxResult


@BusFactory.register
class ReadoutBus(BusDriver):
    """Qililab's driver for Readout Bus"""

    def __init__(
        self,
        alias: str,
        qubit: int,
        awg: AWG,
        digitiser: Digitiser,
        local_oscillator: LocalOscillator | None,
        attenuator: Attenuator | None,
    ):
        """Initialise the bus.

        Args:
            alias (str): Bus alias
            qubit (int): Qubit
            awg (AWG): Arbitrary Wave Generator instance
            digitiser (Digitiser): Arbitrary Wave Generator instance to acquire results
            local_oscillator (LocalOscillator): Local Oscillator
            attenuator (Attenuator): Attenuator
        """
        super().__init__(alias=alias, qubit=qubit, awg=awg)
        self._digitiser = digitiser
        self.instruments["digitiser"] = self._digitiser
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator

    def __str__(self):
        """String representation of a ReadoutBus. Prints a drawing of the bus elements."""
        return f"ReadoutBus {self.alias}: " + "".join(
            f"--|{instrument}|----" for instrument in self.instruments.values()
        )

    def acquire_results(self) -> QbloxResult:
        """Acquires results through the Digitiser Instrument.

        Returns:
            results (QbloxResult): acquisitions of results
        """
        return self._digitiser.get_results()
