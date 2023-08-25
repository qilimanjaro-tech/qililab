"""Driver for the Drive Bus class."""
from copy import deepcopy

from qililab.drivers.interfaces import AWG, Attenuator, Digitiser, LocalOscillator
from qililab.drivers.interfaces.base_instrument import BaseInstrument
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

    @classmethod
    def from_dict(cls, dictionary: dict, instruments: list[BaseInstrument]) -> "ReadoutBus":
        """Loads the ReadoutBus class and sets the instrument params to the corresponding instruments, given a dictionary

        Args:
            dictionary (dict): Dictionary representation of the ReadoutBus object and its instrument params.
            instruments (dict[str, BaseInstrument | None]): Instruments that are already initialized in dictionary, with its name as a str key.

        Returns:
            ReadoutBus: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("type", None)

        # Transform the instrument str into the corresponding classes for the dictionary, and set its parameters.
        local_dictionary = super().bus_instruments_str_to_classes_and_set_params(
            dictionary=local_dictionary, instruments=instruments
        )

        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Generates a dict representation given the Buses and the instruments params of such bus.

        Returns:
            dict: Bus dictionary with its corresponding instrument parameters.
        """
        bus_dictionary_start: dict = {
            "alias": self.alias,
            "type": self.__class__.__name__,
        }

        instruments_list = [instrument for instrument in self.instruments.values() if instrument is not None]
        instruments_dictionary = super().bus_instruments_classes_to_str_and_get_params(
            instruments=instruments_list
        )  # Get the instruments dictionary.

        for key in instruments_dictionary:
            assert key in ("AWG", "Digitiser", "LocalOscillator", "Attenuator")

        bus_dictionary_end = {
            "port": self.port,
            "distortions": [distortion.to_dict() for distortion in self.distortions],
        }

        return bus_dictionary_start | instruments_dictionary | bus_dictionary_end
