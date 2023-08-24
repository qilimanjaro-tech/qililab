"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, Attenuator, Digitiser, LocalOscillator
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory
from qililab.result.qblox_results.qblox_result import QbloxResult


@BusFactory.register
class ReadoutBus(BusDriver):
    """Qililab's driver for Readout Bus"""

    def __init__(
        self,
        alias: str,
        port: int,
        awg: AWG,
        digitiser: Digitiser,
        local_oscillator: LocalOscillator | None,
        attenuator: Attenuator | None,
    ):
        """Initialise the bus.

        Args:
            alias (str): Bus alias
            port (int): Port to target
            awg (AWG): Arbitrary Wave Generator instance
            digitiser (Digitiser): Arbitrary Wave Generator instance to acquire results
            local_oscillator (LocalOscillator): Local Oscillator
            attenuator (Attenuator): Attenuator
        """
        super().__init__(alias=alias, port=port, awg=awg)
        self._digitiser = digitiser
        self.instruments["digitiser"] = self._digitiser
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator

    def acquire_results(self) -> QbloxResult:
        """Acquires results through the Digitiser Instrument.

        Returns:
            results (QbloxResult): acquisitions of results
        """
        return self._digitiser.get_results()

    def to_dict(self, instruments):
        """Generates a dict representation given the Buses and the instruments get_parms()"""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, dictionary: dict) -> "ReadoutBus":
        """Generates the ReadoutBus class and passes the instrument params info to be set with set_params(), given a dictionary"""
        _ = dict
        raise NotImplementedError
