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
from __future__ import annotations

import contextlib
from dataclasses import InitVar, dataclass
from typing import TYPE_CHECKING

from qililab.constants import RUNCARD
from qililab.exceptions import ParameterNotFound
from qililab.settings import Settings

if TYPE_CHECKING:
    from qpysequence import Sequence as QpySequence

    from qililab.instruments.instrument import Instrument
    from qililab.instruments.instruments import Instruments
    from qililab.result import Result
    from qililab.result.qprogram.measurement_result import MeasurementResult
    from qililab.typings.enums import Parameter


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
            distortions (list[PulseDistotion]): List of the distortions to apply to the Bus.
            delay (int): Bus delay
        """

        alias: str
        instruments: list[Instrument]
        channels: list[int | str | None]
        platform_instruments: InitVar[Instruments]

        def __post_init__(self, platform_instruments: Instruments):  # type: ignore # pylint: disable=arguments-differ
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
            super().__post_init__()

    settings: BusSettings
    """Bus settings. Containing the alias of the bus, the system control used to control and readout its qubits, the
    list of the distortions to apply, and its delay.
    """

    def __init__(self, settings: dict, platform_instruments: Instruments):
        self.settings = self.BusSettings(**settings, platform_instruments=platform_instruments)  # type: ignore

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
    def channels(self) -> list[int | str | None]:
        """Instruments controlled by this system control."""
        return self.settings.channels

    def __str__(self):
        """String representation of a bus. Prints a drawing of the bus elements."""
        instruments = "--".join(f"|{instrument}|" for instrument in self.instruments)
        return f"Bus {self.alias}:  ----{instruments}----"

    def __eq__(self, other: object) -> bool:
        """compare two Bus objects"""
        return str(self) == str(other) if isinstance(other, Bus) else False

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(self.instruments)

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

    def set_parameter(self, parameter: Parameter, value: int | float | str | bool, channel_id: int | str | None = None):
        """Set a parameter to the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            with contextlib.suppress(ParameterNotFound):
                if channel_id is not None and channel_id == instrument_channel:
                    instrument.set_parameter(parameter, value, channel_id)
                    return
                instrument.set_parameter(parameter, value, instrument_channel)
                return
        raise ParameterNotFound(
            f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}"
        )

    def get_parameter(self, parameter: Parameter, channel_id: int | str | None = None):
        """Gets a parameter of the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            with contextlib.suppress(ParameterNotFound):
                if channel_id is not None and channel_id == instrument_channel:
                    return instrument.get_parameter(parameter, channel_id)
                return instrument.get_parameter(parameter, instrument_channel)
        raise ParameterNotFound(
            f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}"
        )

    def upload_qpysequence(self, qpysequence: QpySequence, channel_id: int | str | None = None):
        """Uploads the qpysequence into the instrument."""
        from qililab.instruments.qblox.qblox_module import QbloxModule  # pylint: disable=import-outside-toplevel

        for instrument, instrument_channel in zip(self.instruments, self.channels):
            if isinstance(instrument, QbloxModule):
                if channel_id is not None and channel_id == instrument_channel:
                    instrument.upload_qpysequence(qpysequence=qpysequence, channel_id=channel_id)
                    return
                instrument.upload_qpysequence(qpysequence=qpysequence, channel_id=instrument_channel)
                return

        raise AttributeError(f"Bus {self.alias} doesn't have any QbloxModule to upload a qpysequence.")

    def upload(self):
        """Uploads any previously compiled program into the instrument."""
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            if instrument.is_awg():
                instrument.upload(instrument_channel)
                return

    def run(self) -> None:
        """Runs any previously uploaded program into the instrument."""
        for instrument, instrument_channel in zip(self.instruments, self.channels):
            if instrument.is_awg():
                instrument.as_awg().run(channel_id=instrument_channel)
                return

    def acquire_result(self) -> Result:
        """Read the result from the vector network analyzer instrument

        Returns:
            Result: Acquired result
        """
        # TODO: Support acquisition from multiple instruments
        results: list[Result] = []
        for instrument in self.instruments:
            if instrument.is_adc():
                result = instrument.as_adc().acquire_result()
                if result is not None:
                    results.append(result)

        if len(results) > 1:
            raise ValueError(
                f"Acquisition from multiple instruments is not supported. Obtained a total of {len(results)} results. "
            )

        if len(results) == 0:
            raise AttributeError(f"The bus {self.alias} cannot acquire results.")

        return results[0]

    def acquire_qprogram_results(self, acquisitions: list[str]) -> list[MeasurementResult]:
        """Read the result from the instruments

        Returns:
            list[Result]: Acquired results in chronological order
        """
        # TODO: Support acquisition from multiple instruments
        total_results: list[list[MeasurementResult]] = []
        for instrument in self.instruments:
            if instrument.is_adc():
                instrument_results = instrument.as_adc().acquire_qprogram_results(acquisitions=acquisitions)
                total_results.append(instrument_results)

        if len(total_results) == 0:
            raise AttributeError(
                f"The bus {self.alias} cannot acquire results because it doesn't have a readout system control."
            )

        return total_results[0]
