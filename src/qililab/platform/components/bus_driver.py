"""Bus Class Interface."""
from copy import deepcopy
from typing import Any

from qililab.drivers.interfaces import AWG, BaseInstrument
from qililab.drivers.interfaces.instrument_interface_factory import InstrumentInterfaceFactory
from qililab.pulse import PulseBusSchedule, PulseDistortion
from qililab.typings.factory_element import FactoryElement

from .bus_factory import BusFactory


class BusDriver(FactoryElement):
    """Bus Class.

    Args:
        alias (str): Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        distortions (list): Distortions to apply in this Bus.
    """

    def __init__(self, alias: str, port: int, awg: AWG | None, distortions: list):
        """Initialise the base of a bus."""
        self.alias = alias
        self.port = port
        self._awg = awg
        self.instruments: dict[str, BaseInstrument | None] = {"awg": self._awg}
        self.delay: int = 0
        self.distortions: list[PulseDistortion] = [
            PulseDistortion.from_dict(distortion) if isinstance(distortion, dict) else distortion
            for distortion in distortions
        ]

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

    @classmethod
    def convert_instruments_strings_to_classes_and_set_params(
        cls, dictionary: dict, instruments: list[BaseInstrument]
    ) -> dict:
        """Passes the strings of the instruments associated to the bus, into their corresponding (already instantiated)
        classes throught their "alias". While it also sets their corresponding given parameters.

        And finally returns a dictionary with only the instruments classes.

        Passes the instruments classes associated with the bus, into their corresponding strings. While it
        also gets all their corresponding parameters to be printed together in a dictionary.

        The dictionary reading follows the following diagram: (Picture)[https://imgur.com/a/U4Oyapo]

        Args:
            dictionary (dict): Bus dictionary with the instruments as strings.
            instruments (list[BaseInstrument]): Already instantiated instruments.

        Returns:
            dict: Bus dictionary with the instruments as classes to be inserted in the bus dictionary.
        """
        instruments_dictionary: dict[str, BaseInstrument] = {}
        memorized_keys: list[str] = []

        for key, instrument_dict in dictionary.items():
            if key in cls.caps_translate_dict():
                memorized_keys.append(key)
                for instrument in instruments:
                    if (
                        issubclass(instrument.__class__, InstrumentInterfaceFactory.get(key))
                        and instrument.alias == instrument_dict["alias"]
                    ):
                        for parameter, value in instrument_dict["parameters"].items():
                            instrument.set(param_name=parameter, value=value)

                        instruments_dictionary[cls.caps_translate_dict()[key]] = instrument
                        break

        for key in memorized_keys:
            dictionary.pop(key)

        return dictionary | instruments_dictionary

    @classmethod
    def convert_instruments_classes_to_strings_and_get_params(
        cls, instruments: list[BaseInstrument]
    ) -> dict[str, dict]:
        """Passes the instruments classes associated to the bus, into their corresponding strings. While it
        also gets all their corresponding parameters to be printed together in a dictionary.

        And finally returns a dictionary with the instrument str as key (str), and the alias and parameters as values (dict).

        The dictionary construction follows the following diagram: (Picture)[https://imgur.com/a/U4Oyapo]

        Args:
            instruments (list[BaseInstrument]): Instruments corresponding the the given Bus.

        Returns:
            dict[str, dict]: The instruments dictionary to be inserted in the bus dictionary. Keys are the instruments str,
                and values are an inner dictionary containing the alias and the parameters dictionary.
        """
        instruments_dict: dict[str, dict] = {}
        for instrument in instruments:
            if instrument is not None:
                instrument_dict = {"alias": instrument.alias}

                if instrument.params:
                    params_dict = {
                        parameter: instrument.get(parameter)
                        for parameter in instrument.params.keys()
                        if parameter
                        not in (
                            "IDN",
                            "sequence",
                        )  # skip IDN and sequence parameters. Which will go into other parts of the runcard.
                    }
                if params_dict:
                    instrument_dict["parameters"] = params_dict

                for key in cls.caps_translate_dict():
                    if issubclass(instrument.__class__, InstrumentInterfaceFactory.get(key)):
                        instruments_dict[key] = instrument_dict

        return instruments_dict

    @classmethod
    def from_dict(cls, dictionary: dict, instruments: list[BaseInstrument]) -> "BusDriver":
        """Loads the corresponding Bus driver class with a Factory Pattern, and sets the instrument params to the corresponding instruments.

        Args:
            dictionary (dict): Dictionary representation of the Bus driver object and its instrument params.
            instruments (list[BaseInstrument]): Already instantiated instruments.

        Returns:
            BusDriver: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("type", None)

        # Transform the instrument str into the corresponding classes for the dictionary, and set its parameters.
        local_dictionary = cls.convert_instruments_strings_to_classes_and_set_params(
            dictionary=local_dictionary, instruments=instruments
        )

        return BusFactory.get(name=dictionary["type"])(**local_dictionary)  # type: ignore[return-value]

    def to_dict(self) -> dict:
        """Generates a dict representation given the Buses and the instruments params of such bus.

        Returns:
            dict: Bus dictionary with its corresponding instrument parameters.
        """
        bus_dictionary_start: dict = {
            "alias": self.alias,
            "type": self.__class__.__name__,
        }

        # Get the instruments dictionary.
        instruments_list = [instrument for instrument in self.instruments.values() if instrument is not None]
        instruments_dictionary = self.convert_instruments_classes_to_strings_and_get_params(
            instruments=instruments_list
        )

        bus_dictionary_end = {
            "port": self.port,
            "distortions": [distortion.to_dict() for distortion in self.distortions],
        }

        return bus_dictionary_start | instruments_dictionary | bus_dictionary_end

    @staticmethod
    def caps_translate_dict() -> dict:
        """Dictionary to translate the instruments[str] to the caps showing in the Runcard (for aesthetics)."""
        return {
            "AWG": "awg",
            "Digitiser": "digitiser",
            "LocalOscillator": "local_oscillator",
            "Attenuator": "attenuator",
            "VoltageSource": "voltage_source",
            "CurrentSource": "current_source",
        }
