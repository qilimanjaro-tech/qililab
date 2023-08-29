"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, Attenuator, Digitiser, LocalOscillator
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory
from qililab.result.qblox_results.qblox_result import QbloxResult


@BusFactory.register
class ReadoutBus(BusDriver):
    """Qililab's driver for Readout Bus

    Args:
        alias: Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        digitiser (Digitiser): Arbitrary Wave Generator instance to acquire results.
        local_oscillator (LocalOscillator | None): Local oscillator.
        attenuator (Attenuator | None): Attenuator.
        distortions (list): Distortions to apply in this Bus.

    Returns:
        BusDriver: BusDriver instance of type readout bus.
    """

    def __init__(
        self,
        alias: str,
        port: int,
        awg: AWG,
        digitiser: Digitiser,
        local_oscillator: LocalOscillator | None,
        attenuator: Attenuator | None,
        distortions: list,
    ):
        """Initialise the bus."""
        super().__init__(alias=alias, port=port, awg=awg, distortions=distortions)
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
