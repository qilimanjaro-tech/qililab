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

from qililab.instruments.instrument2 import Instrument2
from qililab.runcard import RuncardBus
from qililab.settings.buses import BusSettings
from qililab.typings import Parameter, ParameterValue


class Bus:
    _settings: BusSettings
    _instruments: list[Instrument2]
    _channels: list[int | str | None]

    def __init__(self, settings: BusSettings, loaded_instruments: list[Instrument2] | None = None):
        self._settings = settings
        self._instruments = []
        self._channels = []
        if loaded_instruments is not None:
            self.load_instruments(loaded_instruments)

    @property
    def alias(self):
        return self._settings.alias

    @property
    def settings(self):
        return self._settings

    @property
    def connected_instruments_and_channels(self) -> list[tuple[Instrument2, int | str | None]]:
        return list(zip(self._instruments, self._channels))

    def load_instruments(self, instruments: list[Instrument2]):
        for instrument_alias, channel in list(zip(self.settings.instruments, self.settings.channels)):
            instrument = next(
                (instrument for instrument in instruments if instrument.settings.alias == instrument_alias), None
            )
            if instrument is None:
                raise ValueError(f"No instrument found with alias {instrument_alias}.")
            self._instruments.append(instrument)
            self._channels.append(channel)

    def set_parameter(self, parameter: Parameter, value: ParameterValue):
        for instrument, channel in self.connected_instruments_and_channels:
            if parameter in instrument.get_instrument_parameters():
                instrument.set_parameter(parameter=parameter, value=value)
            if channel is not None and parameter in instrument.get_channel_parameters():
                instrument.set_parameter(parameter=parameter, value=value, channel=channel)

    def get_parameter(self, parameter: Parameter):
        for instrument, channel in self.connected_instruments_and_channels:
            if parameter in instrument.get_instrument_parameters():
                return instrument.get_parameter(parameter=parameter)
            if channel is not None and parameter in instrument.get_channel_parameters():
                return instrument.get_parameter(parameter=parameter, channel=channel)
        return None

    def to_runcard(self) -> RuncardBus:
        return self.settings
