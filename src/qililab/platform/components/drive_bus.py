"""Driver for the Drive Bus class."""
from copy import deepcopy

from qililab.drivers.interfaces.attenuator import Attenuator
from qililab.drivers.interfaces.awg import AWG
from qililab.drivers.interfaces.base_instrument import BaseInstrument
from qililab.drivers.interfaces.local_oscillator import LocalOscillator
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class DriveBus(BusDriver):
    """Qililab's driver for Drive Bus.

    Args:
        alias: Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        local_oscillator (LocalOscillator | None): Local oscillator.
        attenuator (Attenuator | None): Attenuator.
        distortions (list): Distortions to apply in this Bus.

    Returns:
        BusDriver: BusDriver instance of type drive bus.
    """

    def __init__(
        self,
        alias: str,
        port: int,
        awg: AWG,
        local_oscillator: LocalOscillator | None,
        attenuator: Attenuator | None,
        distortions: list,
    ):
        """Initialise the bus."""
        super().__init__(alias=alias, port=port, awg=awg, distortions=distortions)
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator

    @classmethod
    def from_dict(cls, dictionary: dict, instruments: list[BaseInstrument]) -> "DriveBus":
        """Loads the DriveBus class and sets the instrument params to the corresponding instruments, given a dictionary

        Args:
            dictionary (dict): Dictionary representation of the DriveBus object and its instrument params.
            instruments (dict[str, BaseInstrument | None]): Instruments that are already initialized in dictionary, with its name as a str key.

        Returns:
            DriveBus: Loaded class.
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
            assert key in ("AWG", "LocalOscillator", "Attenuator")

        bus_dictionary_end = {
            "port": self.port,
            "distortions": [distortion.to_dict() for distortion in self.distortions],
        }

        return bus_dictionary_start | instruments_dictionary | bus_dictionary_end
