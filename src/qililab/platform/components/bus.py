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

"""Bus class."""

import contextlib
from dataclasses import InitVar, dataclass, field

from qpysequence import Sequence as QpySequence

from qililab.constants import RUNCARD
from qililab.instruments import Instrument, Instruments, ParameterNotFound
from qililab.instruments.qblox import QbloxQCM, QbloxQRM
from qililab.pulse.pulse_distortion.pulse_distortion import PulseDistortion
from qililab.qprogram.qblox_compiler import AcquisitionData
from qililab.result import Result
from qililab.result.qprogram import MeasurementResult
from qililab.settings import Settings
from qililab.typings import FILTER_PARAMETERS, ChannelID, OutputID, Parameter, ParameterValue


class Bus:
    """Bus class.

    Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    @dataclass
    class BusSettings(Settings):
        """Bus settings.

        Args:
            alias (str): Alias of the bus.
            system_control (SystemControl): System control used to control and readout the qubits of the bus.
            port (str): Alias of the port where bus is connected.
            distortions (list[PulseDistotion]): List of the distortions to apply to the Bus.
            delay (int): Bus delay
        """

        alias: str
        instruments: list[Instrument]
        channels: list[ChannelID | None]
        platform_instruments: InitVar[Instruments]
        delay: int = 0
        distortions: list[PulseDistortion] = field(default_factory=list)

        def __post_init__(self, platform_instruments: Instruments):  # type: ignore
            instruments = []
            for inst_alias in self.instruments:
                inst_class = platform_instruments.get_instrument(alias=inst_alias)  # type: ignore
                if inst_class is None:
                    raise NameError(
                        f"The instrument with alias {inst_alias} could not be found within the instruments of the "
                        "platform. The available instrument aliases are: "
                        f"{[inst.alias for inst in platform_instruments.elements]}."
                    )
                instruments.append(inst_class)
            self.instruments = instruments
            self.distortions = [
                PulseDistortion.from_dict(distortion)  # type: ignore[arg-type]
                for distortion in self.distortions
                if isinstance(distortion, dict)
            ]
            super().__post_init__()

    settings: BusSettings
    """Bus settings. Containing the alias of the bus, the system control used to control and readout its qubits, the alias
    of the port where it's connected, the list of the distortions to apply, and its delay.
    """

    def __init__(self, settings: dict, platform_instruments: Instruments):
        self.settings = self.BusSettings(**settings, platform_instruments=platform_instruments)  # type: ignore[call-arg]

    @property
    def alias(self):
        """Alias of the bus.

        Returns:
            str: alias of the bus
        """
        return self.settings.alias

    @property
    def instruments(self) -> list[Instrument]:
        """Instruments controlled by this system control."""
        return self.settings.instruments

    @property
    def channels(self) -> list[ChannelID | None]:
        """Instruments controlled by this system control."""
        return self.settings.channels

    @property
    def delay(self):
        """Bus 'delay' property.

        Returns:
            int: settings.delay.
        """
        return self.settings.delay

    @property
    def distortions(self):
        """Bus 'distortions' property.

        Returns:
            list[PulseDistortion]: settings.distortions.
        """
        return self.settings.distortions

    def __str__(self):
        """String representation of a bus. Prints a drawing of the bus elements."""
        instruments = "--".join(f"|{instrument}|" for instrument in self.instruments)
        return f"Bus {self.alias}:  ----{instruments}----"

    def __eq__(self, other: object) -> bool:
        """compare two Bus objects"""
        return str(self) == str(other) if isinstance(other, Bus) else False

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(zip(self.instruments, self.channels))

    def to_dict(self):
        """Return a dict representation of the Bus class."""
        return {
            RUNCARD.ALIAS: self.alias,
            RUNCARD.INSTRUMENTS: [instrument.alias for instrument in self.instruments],
            "channels": self.settings.channels,
        }

    def has_awg(self) -> bool:
        """Return true if bus has AWG capabilities."""
        return any(instrument.is_awg() for instrument in self.instruments)

    def has_adc(self) -> bool:
        """Return true if bus has ADC capabilities."""
        return any(instrument.is_adc() for instrument in self.instruments)

    def _get_outputid_from_channelid(self) -> int:
        "Returns the output_id associated with the sequencer linked to the bus in use"
        for sequencer in self.settings.instruments[0].awg_sequencers:  # type: ignore[attr-defined]
            if sequencer.identifier == self.channels[0]:
                return sequencer.outputs[0]
        raise Exception(f"No output_id was found to be associated with the bus with alias {self.alias}")

    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None, output_id: OutputID | None = None):
        """Set a parameter to the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int, optional): instrument channel to update, if multiple. Defaults to None.
            output_id (int): module id. Defaults to None.
        """
        if parameter in FILTER_PARAMETERS:
            bus_output_id = self._get_outputid_from_channelid()
            if channel_id is not None:
                raise Exception("Filter parameters are controlled using output_id and not channel_id")
            if output_id is not None and output_id == bus_output_id:
                self.instruments[0].set_parameter(parameter=parameter, value=value, output_id=output_id)
                return
            if output_id is not None and output_id != bus_output_id:
                raise Exception(f"OutputID {output_id} is not linked to bus with alias {self.alias}")
            self.instruments[0].set_parameter(parameter=parameter, value=value, output_id=bus_output_id)
            return
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            with contextlib.suppress(ParameterNotFound):
                if output_id is not None:
                    raise Exception("Only QBlox Filter parameters are controlled using output_id and not channel_id")
                if channel_id is not None and channel_id == instrument_channel:
                    instrument.set_parameter(parameter, value, channel_id)
                    return
                if channel_id is not None and channel_id not in self.channels:
                    raise Exception(f"ChannelID {channel_id} is not linked to bus with alias {self.alias}")
                instrument.set_parameter(parameter, value, instrument_channel)
                return
        raise Exception(f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}")

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None, output_id: OutputID | None = None):
        """Gets a parameter of the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int, optional): instrument channel to update, if multiple. Defaults to None.
            output_id (int): module id. Defaults to None.
        """
        if parameter == Parameter.DELAY:
            return self.settings.delay

        if parameter in FILTER_PARAMETERS:
            bus_output_id = self._get_outputid_from_channelid()
            if channel_id is not None:
                raise Exception("Filter parameters are controlled using output_id and not channel_id")
            if output_id is not None and output_id == bus_output_id:
                return self.instruments[0].get_parameter(parameter=parameter, output_id=output_id)
            if output_id is not None and output_id != bus_output_id:
                raise Exception(f"OutputID {output_id} is not linked to bus with alias {self.alias}")
            return self.instruments[0].get_parameter(parameter=parameter, output_id=bus_output_id)

        for instrument, instrument_channel in zip(self.instruments, self.channels):
            with contextlib.suppress(ParameterNotFound):
                if output_id is not None:
                    raise Exception("Only QBlox Filter parameters are controlled using output_id and not channel_id")
                if channel_id is not None and channel_id == instrument_channel:
                    return instrument.get_parameter(parameter, channel_id)
                if channel_id is not None and channel_id not in self.channels:
                    raise Exception(f"ChannelID {channel_id} is not linked to bus with alias {self.alias}")
                return instrument.get_parameter(parameter, instrument_channel)
        raise Exception(f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}")

    def upload_qpysequence(self, qpysequence: QpySequence):
        """Uploads the qpysequence into the instrument."""
        from qililab.instruments.qblox.qblox_module import QbloxModule  # pylint: disable=import-outside-toplevel

        for instrument, instrument_channel in zip(self.instruments, self.channels):
            if isinstance(instrument, QbloxModule):
                instrument.upload_qpysequence(qpysequence=qpysequence, channel_id=int(instrument_channel))  # type: ignore[arg-type]
                return

        raise AttributeError(f"Bus {self.alias} doesn't have any QbloxModule to upload a qpysequence.")

    def upload(self):
        """Uploads any previously compiled program into the instrument."""
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            if isinstance(instrument, (QbloxQCM, QbloxQRM)):
                instrument.upload(channel_id=instrument_channel)
                return

    def run(self) -> None:
        """Runs any previously uploaded program into the instrument."""
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            if isinstance(instrument, (QbloxQCM, QbloxQRM)):
                instrument.run(channel_id=instrument_channel)  # type: ignore
                return

    def acquire_result(self) -> Result:
        """Read the result from the vector network analyzer instrument

        Returns:
            Result: Acquired result
        """
        # TODO: Support acquisition from multiple instruments
        results: list[Result] = []
        for instrument in self.instruments:
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
        self, acquisitions: dict[str, AcquisitionData], channel_id: ChannelID | None = None
    ) -> list[MeasurementResult]:
        """Read the result from the instruments

        Returns:
            list[Result]: Acquired results in chronological order
            channel_id (int, optional): instrument channel of QRM. Defaults to None.
        """
        # TODO: Support acquisition from multiple instruments
        total_results: list[list[MeasurementResult]] = []
        for instrument in self.instruments:
            if isinstance(instrument, QbloxQRM):
                instrument_results = instrument.acquire_qprogram_results(
                    acquisitions=acquisitions, channel_id=channel_id
                )
                total_results.append(instrument_results)

        if len(total_results) == 0:
            raise AttributeError(
                f"The bus {self.alias} cannot acquire results because it doesn't have a readout system control."
            )

        return total_results[0]

    def _setup_trigger_network(self, trigger_address):
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            if isinstance(instrument, (QbloxQRM)):
                instrument._setup_trigger_network(trigger_address=trigger_address, sequencer_id=instrument_channel)
                return
