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

from typing import TYPE_CHECKING

from qililab.buses.aggregated_bus_parameter import AggregatedBusParameter
from qililab.instruments.instrument import InstrumentWithChannels
from qililab.instruments.qblox_qcm import QbloxQCM
from qililab.instruments.qblox_qrm import QbloxQRM

if TYPE_CHECKING:
    from qpysequence import Sequence as QpySequence

    from qililab.instruments.instrument import Instrument
    from qililab.qprogram.qblox_compiler import AcquisitionData
    from qililab.result import Result
    from qililab.result.qprogram import MeasurementResult
    from qililab.runcard.runcard_buses import RuncardBus
    from qililab.settings.buses.bus_settings import BusSettings
    from qililab.typings import Parameter, ParameterValue


class Bus:
    _settings: BusSettings
    _instruments: list[Instrument]
    _channels: list[int | str | None]
    parameters: dict[str, AggregatedBusParameter]

    def __init__(self, settings: BusSettings, loaded_instruments: list[Instrument] | None = None):
        self._settings = settings
        self._instruments = []
        self._channels = []
        self.parameters = {}
        if loaded_instruments is not None:
            self.load_instruments(loaded_instruments)

    @property
    def alias(self):
        return self._settings.alias

    @property
    def settings(self):
        return self._settings

    @property
    def instruments(self):
        return self._instruments

    @property
    def channels(self):
        return self._channels

    def has_awg(self):
        return True

    def has_adc(self):
        return True

    def instruments_and_channels(self) -> list[tuple[Instrument, int | str | None]]:
        return list(zip(self._instruments, self._channels))

    def load_instruments(self, instruments: list[Instrument]):
        for instrument_alias, channel in list(zip(self.settings.instruments, self.settings.channels)):
            instrument = next(
                (instrument for instrument in instruments if instrument.settings.alias == instrument_alias), None
            )
            if instrument is None:
                raise ValueError(f"No instrument found with alias {instrument_alias}.")
            self._instruments.append(instrument)
            self._channels.append(channel)

            if not hasattr(self, instrument_alias):
                setattr(self, instrument_alias, instrument)

        self._attach_aggregated_parameters()

    def _attach_aggregated_parameters(self):
        # Gather all parameter names from instruments and their associated channels
        parameter_names = set()
        for instrument, channel_id in self.instruments_and_channels():
            # Add top-level instrument parameters
            parameter_names.update(instrument.parameters.keys())

            # If the bus is connected to a channel, include that channel's parameters too
            if channel_id is not None and isinstance(instrument, InstrumentWithChannels):
                channel = instrument.channels.get(channel_id)
                if channel is not None:
                    parameter_names.update(channel.parameters.keys())

        # Create a bus-level parameter for each discovered parameter name
        for name in parameter_names:
            if not hasattr(self, name):
                parameter = AggregatedBusParameter(name=name, bus=self)
                self.parameters[name] = parameter
                setattr(self, name, parameter)

    def set_parameter(self, parameter: Parameter, value: ParameterValue):
        for instrument, channel in self.instruments_and_channels():
            if parameter in instrument.get_instrument_parameters():
                instrument.set_parameter(parameter=parameter, value=value)
            if channel is not None and parameter in instrument.get_channel_parameters():
                instrument.set_parameter(parameter=parameter, value=value, channel=channel)

    def get_parameter(self, parameter: Parameter):
        for instrument, channel in self.instruments_and_channels():
            if parameter in instrument.get_instrument_parameters():
                return instrument.get_parameter(parameter=parameter)
            if channel is not None and parameter in instrument.get_channel_parameters():
                return instrument.get_parameter(parameter=parameter, channel=channel)
        return None

    def to_runcard(self) -> RuncardBus:
        return self.settings

    def upload_qpysequence(self, qpysequence: QpySequence):
        """Uploads the qpysequence into the instrument."""
        from qililab.instruments.qblox_module import QbloxModule  # pylint: disable=import-outside-toplevel

        for instrument, instrument_channel in self.instruments_and_channels():
            if isinstance(instrument, QbloxModule):
                instrument.upload_qpysequence(qpysequence=qpysequence, sequencer_id=int(instrument_channel))  # type: ignore[arg-type]
                return

        raise AttributeError(f"Bus {self.alias} doesn't have any QbloxModule to upload a qpysequence.")

    def upload(self):
        """Uploads any previously compiled program into the instrument."""
        for instrument, instrument_channel in self.instruments_and_channels():
            if isinstance(instrument, (QbloxQCM, QbloxQRM)):
                instrument.upload(sequencer_id=instrument_channel)
                return

    def run(self) -> None:
        """Runs any previously uploaded program into the instrument."""
        for instrument, instrument_channel in self.instruments_and_channels():
            if isinstance(instrument, (QbloxQCM, QbloxQRM)):
                instrument.run(sequencer_id=instrument_channel)  # type: ignore
                return

    def acquire_result(self) -> Result:
        """Read the result from the vector network analyzer instrument

        Returns:
            Result: Acquired result
        """
        # TODO: Support acquisition from multiple instruments
        results: list[Result] = []
        for instrument, _ in self.instruments_and_channels():
            if isinstance(instrument, QbloxQRM):
                result = instrument.acquire_result()
                if result is not None:
                    results.append(result)

        if len(results) > 1:
            raise ValueError(
                f"Acquisition from multiple instruments is not supported. Obtained a total of {len(results)} results."
            )

        if len(results) == 0:
            raise AttributeError(f"The bus {self.alias} cannot acquire results.")

        return results[0]

    def acquire_qprogram_results(
        self, acquisitions: dict[str, AcquisitionData], channel_id: int | str | None = None
    ) -> list[MeasurementResult]:
        """Read the result from the instruments

        Returns:
            list[Result]: Acquired results in chronological order
            channel_id (int | None, optional): instrument channel of QRM. Defaults to None.
        """
        # TODO: Support acquisition from multiple instruments
        total_results: list[list[MeasurementResult]] = []
        for instrument, _ in self.instruments_and_channels():
            if isinstance(instrument, QbloxQRM):
                instrument_results = instrument.acquire_qprogram_results(
                    acquisitions=acquisitions, sequencer_id=channel_id
                )
                total_results.append(instrument_results)

        if len(total_results) == 0:
            raise AttributeError(
                f"The bus {self.alias} cannot acquire results because it doesn't have a readout system control."
            )

        return total_results[0]
