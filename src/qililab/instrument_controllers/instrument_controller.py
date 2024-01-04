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

"""Instrument Controller class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Callable, Sequence, get_type_hints

from qililab.config import logger
from qililab.constants import INSTRUMENTCONTROLLER, RUNCARD
from qililab.instrument_connections.connection import Connection
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils.instrument_reference import InstrumentReference
from qililab.instruments.utils.loader import Loader
from qililab.platform.components.bus_element import BusElement
from qililab.settings import Settings
from qililab.typings.enums import InstrumentControllerName, Parameter
from qililab.typings.instruments.device import Device
from qililab.utils import Factory


@dataclass(kw_only=True)
class InstrumentControllerSettings(Settings):
    """Contains the settings of a specific Instrument Controller.

    Args:
        connection (Connection): Connection class that represents the connection type of the Instrument Controller.
        modules: (list[InstrumentReference]): List of the Instrument References that links to the actual Instruments
                                                to be managed by the Instrument Controller.
        reset (bool, optional): Whether or not to reset the instrument after connecting to it. Defaults to True.
    """

    alias: str
    connection: Connection
    modules: list[InstrumentReference]
    reset: bool = True

    def __post_init__(self):
        super().__post_init__()
        if self.connection and isinstance(self.connection, dict):
            # Pop the connection name from the dictionary and instantiate its corresponding Connection class.
            self.connection = Factory.get(name=self.connection.pop(RUNCARD.NAME))(settings=self.connection)
        self.modules = [InstrumentReference.from_dict(settings=module) for module in self.modules]


class InstrumentController(BusElement, ABC):
    """Abstract base class declaring the necessary attributes
    and methods for the instrument controllers that manages
    the drivers (device) to one or several instruments and
    the connection to them.

    Args:
        name (InstrumentControllerName): name of the instrument controller
        settings (InstrumentControllerSettings): Settings of the instrument controller.
        device (Device): Driver instance of the instrument to operate the instrument controller.
        number_available_modules (int): Number of modules available in the Instrument Controller.
        modules (Sequence[Instrument]): Actual Instruments classes that manages the Instrument Controller.
        connected_modules_slot_ids (list[int]): List with the slot ids from the connected instruments
    """

    name: InstrumentControllerName
    settings: InstrumentControllerSettings  # a subtype of settings must be specified by the subclass
    device: Device  # a subtype of device must be specified by the subclass
    number_available_modules: int  # to be set by child classes
    modules: Sequence[Instrument]
    connected_modules_slot_ids: list[int]  # slot_id represents the number displayed in the cluster

    class CheckConnected:
        """Property used to check if the connection has established with an instrument."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "InstrumentController", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                AttributeError: If connection has not been established with an instrument.
            """
            ref.connection.check_instrument_is_connected()
            return self._method(ref, *args, **kwargs)

    def __init__(self, settings: dict, loaded_instruments: Instruments):
        settings_class: type[InstrumentControllerSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings)
        self.modules = Loader().replace_modules_from_settings_with_instrument_objects(
            instruments=loaded_instruments,
            instrument_references=self.settings.modules,
        )
        if len(self.modules) <= 0:
            raise ValueError(f"The {self.name.value} Instrument Controller requires at least ONE module.")
        if len(self.modules) > self.number_available_modules:
            raise ValueError(
                f"The {self.name.value} Instrument Controller only supports {self.number_available_modules} module/s."
                + f"You have loaded {len(self.modules)} modules."
            )
        self.connected_modules_slot_ids = self._set_connected_modules_slot_ids()
        if len(self.connected_modules_slot_ids) > self.number_available_modules:
            raise ValueError(
                f"The {self.name.value} Instrument Controller only supports {self.number_available_modules} module/s."
                + f"You have connected {len(self.connected_modules_slot_ids)} modules."
            )
        if len(self.connected_modules_slot_ids) != len(self.modules):
            raise ValueError(
                f"The connected number of modules: {len(self.connected_modules_slot_ids)} differs from "
                + f"the available modules: {len(self.modules)}."
            )

    def _set_connected_modules_slot_ids(self) -> list[int]:
        """Initialize the modules slot ids from the settings"""
        return [instrument_reference.slot_id for instrument_reference in self.settings.modules]

    @abstractmethod
    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""

    @abstractmethod
    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    @abstractmethod
    def _set_device_to_all_modules(self):
        """Sets the initialized device to all modules."""

    def _initialize_device_and_set_to_all_modules(self):
        """Initialize the Controller Device driver and sets it for all modules"""
        self._initialize_device()
        self._set_device_to_all_modules()

    def _release_device_to_all_modules(self):
        """Releases the device to all modules"""
        for module in self.modules:
            module.device = None

    def _release_device_and_set_to_all_modules(self):
        """Release the Controller Device driver and also for all modules"""
        self.device = None
        self._release_device_to_all_modules()

    def set_parameter(
        self,
        parameter: Parameter,
        value: float | str | bool,
        channel_id: int | None = None,  # pylint: disable=unused-argument
    ):
        """Updates the reset settings for the controller."""
        if parameter is not Parameter.RESET:
            raise ValueError("Reset is the only property that can be set for an Instrument Controller.")
        if not isinstance(value, bool):
            raise ValueError("Reset value Must be a boolean.")
        self.settings.reset = value

    def get_parameter(
        self,
        parameter: Parameter,
        channel_id: int | None = None,  # pylint: disable=unused-argument
    ):
        """Updates the reset settings for the controller."""
        if parameter is not Parameter.RESET:
            raise ValueError("Reset is the only property that can be set for an Instrument Controller.")
        return self.settings.reset

    @CheckConnected
    def turn_on(self):
        """Turn on an instrument."""
        for module in self.modules:
            logger.info("Turn on instrument %s.", module.alias or module.name.value)
            module.turn_on()

    @CheckConnected
    def turn_off(self):
        """Turn off an instrument."""
        for module in self.modules:
            logger.info("Turn off instrument %s.", module.alias or module.name.value)
            module.turn_off()

    @CheckConnected
    def reset(self):
        """Reset instrument."""
        for module in self.modules:
            logger.info("Reset instrument %s.", module.alias or module.name.value)
            module.reset()

    @CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        for module in self.modules:
            logger.info("Initial setup to instrument %s.", module.alias or module.name.value)
            module.initial_setup()

    def connect(self):
        """Establishes the connection with the instrument and performs a reset (if necessary)."""
        self._initialize_device_and_set_to_all_modules()
        self.connection.connect(device=self.device, device_name=str(self))
        if self.settings.reset:
            self.reset()

    def disconnect(self):
        """Resets the devices (if needed), close the connection to the instrument and releases the device."""
        if self.settings.reset:
            self.reset()
        self.connection.close()
        self._release_device_and_set_to_all_modules()

    @property
    def alias(self):
        """Instrument Controller 'alias' property.

        Returns:
            str: settings.alias.
        """
        return self.settings.alias

    @property
    def connection(self):
        """Instrument Controller 'connection' property.

        Returns:
            Connection: settings.connection.
        """
        return self.settings.connection

    @property
    def address(self):
        """Instrument Controller 'address' property.

        Returns:
            str: connection.address.
        """
        return self.connection.address

    def __str__(self):
        """String representation of an instrument controller."""
        return f"{self.alias}"

    def to_dict(self):
        """Return a dict representation of the InstrumentReference class."""
        return {
            RUNCARD.NAME: self.name.value,
            RUNCARD.ALIAS: self.alias,
            INSTRUMENTCONTROLLER.CONNECTION: self.connection.to_dict(),
            INSTRUMENTCONTROLLER.MODULES: [module.to_dict() for module in self.settings.modules],
            INSTRUMENTCONTROLLER.RESET: self.settings.reset,
        }
