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

import functools

from qililab.config import logger


def check_device_initialized(func):
    """
    Function decorator to check if the device has been initialized.

    Args:
        method (Callable): The method to be decorated.

    Raises:
        RuntimeError: If the device has not been initialized.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if the device has been initialized.
        if not self.is_device_active():
            logger.error("Instrument: %s | Device has not been initialized.")
            raise RuntimeError(f"Device of instrument {self.alias} has not been initialized.")

        # Call the original function if the device is initialized.
        return func(self, *args, **kwargs)

    return wrapper


def log_set_parameter(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Extract parameters based on whether they are passed positionally or by name
        parameter = kwargs.get("parameter") if "parameter" in kwargs else args[0]
        value = kwargs.get("value") if "value" in kwargs else args[1]
        channel_id = kwargs.get("channel_id") if "channel_id" in kwargs else (args[2] if len(args) > 2 else None)

        # Perform logging
        if channel_id is None:
            logger.debug("Instrument: %s | Setting parameter %s to value %s", self.alias, parameter.value, value)
        else:
            logger.debug(
                "Instrument: %s | Setting parameter %s to value %s in channel %s",
                self.alias,
                parameter.value,
                value,
                channel_id,
            )

        # Call the original function
        return func(self, *args, **kwargs)

    return wrapper
