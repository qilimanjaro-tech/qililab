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

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from qililab.config import logger
from qililab.instruments.instrument2 import Instrument2
from qililab.runcard.runcard_instrument_controllers import RuncardInstrumentController
from qililab.settings.instrument_controllers import InstrumentControllerSettings
from qililab.typings.instruments.device import Device

TDevice = TypeVar("TDevice", bound=Device)
TSettings = TypeVar("TSettings", bound=InstrumentControllerSettings)
TRuncardInstrumentController = TypeVar("TRuncardInstrumentController", bound=RuncardInstrumentController)
TInstrument = TypeVar("TInstrument", bound=Instrument2)


class InstrumentController2(ABC, Generic[TDevice, TSettings, TRuncardInstrumentController, TInstrument]):
    settings: TSettings
    device: TDevice
    modules: list[TInstrument]

    def __init__(self, settings: TSettings | None = None, loaded_instruments: list[TInstrument] | None = None):
        if settings is None:
            settings = self.get_default_settings()
        self.settings = settings
        self.modules = []
        if loaded_instruments is not None:
            self.load_instruments(loaded_instruments)

    @classmethod
    @abstractmethod
    def get_default_settings(cls) -> TSettings:
        pass

    def load_instruments(self, instruments: list[TInstrument]):
        for instrument_module in self.settings.modules:
            instrument = next(
                (instrument for instrument in instruments if instrument.settings.alias == instrument_module.alias), None
            )
            if instrument is None:
                raise ValueError(
                    f"No instrument found for slot {instrument_module.slot} with alias {instrument_module.alias}."
                )
            self.modules.append(instrument)

    @abstractmethod
    def _initialize_device(self):
        pass

    @abstractmethod
    def _set_device_to_all_modules(self):
        pass

    def _initialize_device_and_set_to_all_modules(self):
        """Initialize the Controller Device driver and sets it for all modules"""
        self._initialize_device()
        self._set_device_to_all_modules()

    def _release_device_and_set_to_all_modules(self):
        """Release the Controller Device driver and also for all modules"""
        self.device = None
        for module in self.modules:
            module.device = None

    def connect(self):
        """Establishes the connection with the instrument and performs a reset (if necessary)."""
        self._initialize_device_and_set_to_all_modules()
        self._connected = True
        if self.settings.reset:
            self.reset()

    def disconnect(self):
        """Resets the devices (if needed), close the connection to the instrument and releases the device."""
        if self.settings.reset:
            self.reset()
        self._connected = False
        self._release_device_and_set_to_all_modules()

    def turn_on(self):
        """Turn on an instrument."""
        for module in self.modules:
            logger.info("Turn on instrument %s.", module.alias)
            module.turn_on()

    def turn_off(self):
        """Turn off an instrument."""
        for module in self.modules:
            logger.info("Turn off instrument %s.", module.alias)
            module.turn_off()

    def reset(self):
        """Reset instrument."""
        for module in self.modules:
            logger.info("Reset instrument %s.", module.alias)
            module.reset()

    def initial_setup(self):
        """Initial setup of the instrument."""
        for module in self.modules:
            logger.info("Initial setup to instrument %s.", module.alias)
            module.initial_setup()

    @abstractmethod
    def to_runcard(self) -> TRuncardInstrumentController:
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(settings={self.settings}, modules={self.modules})"
