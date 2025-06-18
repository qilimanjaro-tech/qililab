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

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from qililab.runcard.runcard_controllers import RuncardController
    from qililab.settings.controllers import ControllerSettings

    from .devices import Device

TDevice = TypeVar("TDevice", bound="Device")
TSettings = TypeVar("TSettings", bound="ControllerSettings")


class Controller(ABC, Generic[TDevice, TSettings]):
    device: TDevice
    settings: TSettings

    def __init__(self, settings: TSettings | None = None):
        if settings is None:
            settings = self.get_default_settings()
        self.settings = settings

    @property
    def alias(self):
        return self.settings.alias

    @classmethod
    @abstractmethod
    def get_default_settings(cls) -> TSettings:
        pass

    @abstractmethod
    def _initialize_device(self):
        pass

    def _initialize_device_and_set_to_all_modules(self):
        """Initialize the Controller Device driver and sets it for all modules"""
        self._initialize_device()

    def _release_device_and_set_to_all_modules(self):
        """Release the Controller Device driver and also for all modules"""
        self.device = None

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

    def turn_off(self):
        """Turn off an instrument."""

    def reset(self):
        """Reset instrument."""

    def initial_setup(self):
        """Initial setup of the instrument."""

    @abstractmethod
    def to_runcard(self) -> "RuncardController":
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(settings={self.settings})"
