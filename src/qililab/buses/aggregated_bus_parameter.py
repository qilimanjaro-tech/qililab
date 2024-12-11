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

from typing import TYPE_CHECKING, Any, Dict

from qcodes import Parameter

if TYPE_CHECKING:
    from qililab.buses.bus import Bus


class AggregatedBusParameter(Parameter):
    def __init__(self, name: str, bus: "Bus"):
        """
        A QCoDeS Parameter at the Bus level that aggregates identically
        named parameters present in the bus's instruments and (if specified)
        their connected channels.
        """
        super().__init__(name=name)
        self._bus = bus

    def get_raw(self) -> Dict[str, Any]:
        """
        Return a dict of {instrument_alias: value} for this parameter.
        If the bus is connected to a channel in that instrument, return that channel's parameter value.
        Otherwise, return the instrument's top-level parameter value.
        """
        values = {}
        for instrument, channel_id in self._bus.instruments_and_channels():
            alias = instrument.alias
            if channel_id is not None and hasattr(instrument, "channels"):
                # Channel-level parameter
                channel = instrument.channels.get(channel_id)
                if channel is not None and self.name in channel.parameters:
                    values[alias] = channel.parameters[self.name].get()
                # If the channel doesn't have the parameter, skip it
            else:
                # Top-level instrument parameter
                if self.name in instrument.parameters:
                    values[alias] = instrument.parameters[self.name].get()
                # If the instrument doesn't have the parameter, skip it

        return values

    def set_raw(self, value: Any):
        """
        Set this parameter on all instruments (or their channels, if specified by the bus)
        that have it.
        """
        for instrument, channel_id in self._bus.instruments_and_channels():
            if channel_id is not None and hasattr(instrument, "channels"):
                # Channel-level parameter
                channel = instrument.channels.get(channel_id)
                if channel and self.name in channel.parameters:
                    channel.parameters[self.name].set(value)
            else:
                # Top-level instrument parameter
                if self.name in instrument.parameters:
                    instrument.parameters[self.name].set(value)
