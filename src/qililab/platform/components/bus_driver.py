# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Bus Class Interface."""
from abc import ABC
from copy import deepcopy
from typing import Any

from qililab.drivers.interfaces import AWG, BaseInstrument
from qililab.drivers.interfaces.instrument_interface_factory import InstrumentInterfaceFactory
from qililab.pulse import PulseBusSchedule, PulseDistortion


class BusDriver(ABC):
    """Derived: :class:`DriveBus`, :class:`FluxBus` and :class:`ReadoutBus`

    Bus abstract base class.

    Args:
        alias (str): Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        distortions (list): Distortions to apply in this Bus.
    """

    def __init__(self, alias: str, port: int, awg: AWG | None, distortions: list):
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

    @classmethod
    def from_dict(cls, dictionary: dict, instruments: list[BaseInstrument]) -> "BusDriver":
        """Loads the corresponding BusDriver class and sets the instrument parameters for the corresponding instruments.

        The input dictionary should conform to the following structure: [https://imgur.com/a/U4Oyapo]

        .. code-block:: yaml

            alias: bus_example
            type: DriveBus
            AWG:
                alias: q0_readout
                parameters:
                    gain: 0.9
                    ...
            LO:
                alias: lo_readout
                parameters:
                    frequency: 1e9
                    ...
            Attenuator:
                alias: attenuator_0
                parameters:
                    attenuation: 20
                    ...
            port: 100
            distortions: []

        To correctly set the instrument parameters, the instrument alias (`q0_readout`, ...) and its corresponding
        interface (`AWG`, `LO`, ...) need to match with one of the passed instruments.

        If an instrument serves multiple interfaces, its parameters should be set through only one interface to avoid
        redundancy or to avoid setting them multiple times with different values. However, the (same) alias should be
        specified in all corresponding interfaces.

        The interfaces specified in the dictionary must adhere to the format and sequence outlined in the keys of
        `instrument_interfaces_caps_translate()`. Valid interface types are: AWG, Digitiser, LocalOscillator,
        Attenuator, VoltageSource, and CurrentSource.

        Args:
            dictionary (dict): A dictionary representing the BusDriver object and its instrument parameters.
            instruments (list[BaseInstrument]): A list of pre-instantiated instrument objects.

        Returns:
            BusDriver: The initialized BusDriver class.
        """
        from .bus_factory import BusFactory  # pylint: disable=import-outside-toplevel, cyclic-import

        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("type", None)

        local_dictionary = cls.__convert_instruments_strings_to_classes_and_set_params(
            dictionary=local_dictionary, instruments=instruments
        )

        return BusFactory.get(name=dictionary["type"])(**local_dictionary)  # type: ignore[return-value]

    def to_dict(self) -> dict:
        """Generates a dictionary representation of the Bus and its corresponding instrument parameters.

        The structure of the output dictionary is the following: [https://imgur.com/a/U4Oyapo]

        .. code-block:: yaml

            alias: bus_example
            type: DriveBus
            AWG:
                alias: q0_readout
                parameters:
                    gain: 0.9
                    ...
            LO:
                alias: lo_readout
                parameters:
                    frequency: 1e9
                    ...
            Attenuator:
                alias: attenuator_0
                parameters:
                    attenuation: 20
                    ...
            port: 100
            distortions: []

        The interfaces in the runcard are formatted and ordered according to the keys of `instrument_interfaces_caps_translate()`.
        Acceptable interface types are: AWG, Digitiser, LocalOscillator, Attenuator, VoltageSource, and CurrentSource.

        If an instrument serves multiple interfaces, its parameters will only be included under the first interface
        that appears in the list. However, the alias for that instrument will be repeated across all its interfaces,
        making it easier to associate them.

        The sequence defined in `instrument_interfaces_caps_translate()` is significant because it dictates the order
        in which the parameters are written. Since each instrument's parameters are only saved once, specifically under
        the first interface that appears, the sequence will determine which interface's dictionary entry will include both
        the parameters and the alias, and which will include only the alias.

        Returns:
            dict: A dictionary representing the Bus and its associated instrument parameters.
        """
        bus_dictionary_start: dict = {
            "alias": self.alias,
            "type": self.__class__.__name__,
        }

        instruments_dictionary = self.__convert_instruments_classes_to_strings_and_get_params(
            instruments=[instrument for instrument in self.instruments.values() if instrument is not None]
        )

        bus_dictionary_end = {
            "port": self.port,
            "distortions": [distortion.to_dict() for distortion in self.distortions],
        }

        return bus_dictionary_start | instruments_dictionary | bus_dictionary_end

    @classmethod
    def __convert_instruments_strings_to_classes_and_set_params(
        cls, dictionary: dict, instruments: list[BaseInstrument]
    ) -> dict:
        """Function called in the `from_dict()` method to construct an instance of a bus class from a dictionary.

        Passes the strings of the instruments associated to the bus, into their corresponding (already instantiated)
        classes, through their "alias" and interface. While it also sets their corresponding given parameters.

        To do so, we translate the caps of the instrument interfaces with `instrument_interfaces_caps_translate()`
        (from "AWG" to "awg", from "LocalOscillator" to "local_oscillator", etc...).

        And finally returns a dictionary with only the instruments classes.

        The dictionary reading follows the following structure: [https://imgur.com/a/U4Oyapo], check th `from_dict()`
        documentation for more information regarding this.

        Args:
            dictionary (dict): A dictionary representing the BusDriver object and its instrument parameters.
            instruments (list[BaseInstrument]): A list of pre-instantiated instrument objects.

        Returns:
            dict: Bus dictionary with the instruments as classes to be inserted in the bus dictionary.
        """
        instruments_dictionary: dict[str, BaseInstrument] = {}
        used_keys: list[str] = []

        for key, instrument_dict in dictionary.items():  # pylint: disable=too-many-nested-blocks
            if key in cls.__instrument_interfaces_caps_translate():
                for instrument in instruments:
                    # If the alias and the interface of the dictionary coincide with one of the given instruments:
                    if (
                        issubclass(instrument.__class__, InstrumentInterfaceFactory.get(key))
                        and instrument.alias == instrument_dict["alias"]
                    ):
                        # Set parameters of the initialized instrument
                        if "parameters" in instrument_dict:
                            for parameter, value in instrument_dict["parameters"].items():
                                instrument.set(parameter, value)

                        # Save the instrument classes in the corresponding key, after translating the caps of the interfaces.
                        instruments_dictionary[cls.__instrument_interfaces_caps_translate()[key]] = instrument
                        break

                # Remember used keys, to remove the instrument strings from the original dictionary
                used_keys.append(key)

        for key in used_keys:
            dictionary.pop(key)

        # Add new initialize instrument classes to dictionary
        return dictionary | instruments_dictionary

    @classmethod
    def __convert_instruments_classes_to_strings_and_get_params(
        cls, instruments: list[BaseInstrument]
    ) -> dict[str, dict]:
        """Function called in the `to_dict()` method, to construct a dictionary representing the actual bus instance.

        Passes the instruments classes associated to the bus, into their corresponding strings. While it
        also gets all their corresponding parameters to be printed together in a dictionary.

        To do so, we use the caps format of the instrument interfaces from `instrument_interfaces_caps_translate()`.
        And the order is important here, because it marks the order of writing, and since we only save the parameters
        of each instrument once, concretely in the first interface to appear, this means that the order of
        `__instrument_interfaces_caps_translate()` will indicate in which interface dict you save the
        parameters & alias and in which you only save the alias.

        And finally returns a dictionary with the instrument string as key (str), and the alias and parameters as values (dict).

        The dictionary construction follows the following structure: [https://imgur.com/a/U4Oyapo], check th `to_dict()`
        documentation for more information regarding this.

        Args:
            instruments (list[BaseInstrument]): Instruments corresponding the the given Bus.

        Returns:
            dict[str, dict]: The instruments dictionary to be inserted in the bus dictionary. Keys are the instruments
                strings, and values are an inner dictionary containing the alias and the parameters dictionary.
        """
        instruments_dict: dict[str, dict] = {}
        saved_instruments: set[str] = set()

        # The order of keys marks the writting order and in which interface dict you save the parameters & alias and in which only the alias.
        for key in cls.__instrument_interfaces_caps_translate():
            for instrument in instruments:
                if issubclass(instrument.__class__, InstrumentInterfaceFactory.get(key)):
                    # Add alias of the instrument to the dictionary
                    instruments_dict[key] = {"alias": instrument.alias}

                    # This ensures that instruments with multiple interfaces, don't write the same parameters two times
                    if instrument.alias not in saved_instruments and instrument.params:
                        # Add parameters of the instrument to the dictionary
                        instruments_dict[key]["parameters"] = {
                            parameter: instrument.get(parameter)
                            for parameter in instrument.params.keys()
                            if parameter
                            not in (
                                "IDN",
                                "sequence",
                            )  # skip IDN and sequence parameters. Which will go into other parts of the runcard.
                        }

                    # Save already saved instruments, to not write same parameters twice (in different interfaces)
                    saved_instruments.add(instrument.alias)
                    break

        return instruments_dict

    @staticmethod
    def __instrument_interfaces_caps_translate() -> dict:
        """Dictionary to translate the instruments[str] to the caps showing in the Runcard (for aesthetics).

        The order of the interfaces here determine the order for the printing too, and since we only save the parameters
        of a same instrument once, concretely in the first interface to appear, this means that the order also indicates
        in which interface dict you save the parameters & alias and in which you only save the alias. .
        """
        return {
            "AWG": "awg",
            "Digitiser": "digitiser",
            "LocalOscillator": "local_oscillator",
            "Attenuator": "attenuator",
            "VoltageSource": "source",
            "CurrentSource": "source",
        }

    def __eq__(self, other: object) -> bool:
        """compare two Bus objects"""
        return str(self) == str(other) if isinstance(other, BusDriver) else False

    def __str__(self):
        """String representation of a Bus."""
        return (
            f"{self.alias} ({self.__class__.__name__}): "
            + "".join(f"--|{instrument.alias}|" for instrument in self.instruments.values())
            + f"--> port {self.port}"
        )
