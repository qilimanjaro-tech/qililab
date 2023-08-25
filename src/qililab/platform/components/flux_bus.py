"""Driver for the Drive Bus class."""
from copy import deepcopy

from qililab.drivers.interfaces import AWG, CurrentSource, VoltageSource
from qililab.drivers.interfaces.base_instrument import BaseInstrument
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class FluxBus(BusDriver):
    """Qililab's driver for Flux Bus

    Args:
        alias: Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        source (CurrentSource | VoltageSource): Bus source instrument.
        distortions (list): Distortions to apply in this Bus.

    Returns:
        BusDriver: BusDriver instance of type flux bus.
    """

    def __init__(
        self, alias: str, port: int, awg: AWG | None, source: CurrentSource | VoltageSource | None, distortions: list
    ):
        """Initialise the bus."""
        super().__init__(alias=alias, port=port, awg=awg, distortions=distortions)
        self.instruments["source"] = source

    @classmethod
    def from_dict(cls, dictionary: dict, instruments: list[BaseInstrument]) -> "FluxBus":
        """Loads the FluxBus class and sets the instrument params to the corresponding instruments, given a dictionary

        Args:
            dictionary (dict): Dictionary representation of the FluxBus object and its instrument params.
            instruments (dict[str, BaseInstrument | None]): Instruments that are already initialized in dictionary, with its name as a str key.

        Returns:
            FluxBus: Loaded class.
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
            assert key in ("AWG", "CurrentSource", "VoltageSource")

        bus_dictionary_end = {
            "port": self.port,
            "distortions": [distortion.to_dict() for distortion in self.distortions],
        }

        return bus_dictionary_start | instruments_dictionary | bus_dictionary_end
