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

"""Connection class"""
from abc import ABC
from dataclasses import asdict, dataclass
from functools import partial
from typing import Callable

from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.typings import ConnectionName, Device, FactoryElement


class Connection(ABC, FactoryElement):
    """Abstract base class declaring the necessary attributes and methods for a connection.

    Args:
        name (ConnectionName): type of the Connection.
        settings (ConnectionSettings): Settings of the Connection.
        _connected (bool): True if the instrument is connected.
        _device (Device | None): Device driver to connect to the Instrument.
        _device_name (str): Name of the device to connect to.
    """

    @dataclass
    class ConnectionSettings:
        """Contains the settings of a connection.

        Args:
            address (str): Connection address of the connected device.
        """

        address: str

    name: ConnectionName
    settings: ConnectionSettings  # a subtype of settings must be specified by the subclass

    class CheckConnected:
        """Property used to check if the connection has established with an instrument."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "Connection", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                AttributeError: If connection has not been established with an instrument.
            """
            if not ref._connected:
                raise AttributeError("Instrument is not connected")
            if not hasattr(ref, "_device"):
                raise AttributeError("Instrument Device has not been initialized")
            return self._method(ref, *args, **kwargs)

    def __init__(self, settings: dict):
        self.settings = self.ConnectionSettings(**settings)
        self._connected = False
        self._device: Device | None = None
        self._device_name = ""

    def connect(self, device: Device, device_name: str):
        """Establish connection with the instrument. Initialize self._device variable."""
        if self._connected:
            raise ValueError(f"Instrument ({device_name}) is already connected")
        self._connected = True
        self._device = device
        self._device_name = device_name
        logger.info("Connecting to instrument %s.", self._device_name)

    @CheckConnected
    def close(self):
        """Close an open connection with the instrument. Set self._device to None"""
        logger.info("Closing instrument %s.", self._device_name)
        self._device.close()
        self._connected = False
        self._device = None
        self._device_name = ""

    @property
    def address(self):
        """Connection 'address' property.

        Returns:
            str: settings.address.
        """
        return self.settings.address

    @CheckConnected
    def check_instrument_is_connected(self):
        """check if instrument has been connected and initialized.
        It is checked via a decorator.
        """

    def to_dict(self):
        """Return a dict representation of the Connection class."""
        return {RUNCARD.NAME: self.name.value} | asdict(self.settings)
