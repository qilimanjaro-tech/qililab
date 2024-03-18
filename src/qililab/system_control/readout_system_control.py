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

"""ReadoutSystemControl class."""
from qililab.instruments import AWGAnalogDigitalConverter
from qililab.result import Result
from qililab.typings.enums import SystemControlName
from qililab.utils import Factory

from .system_control import SystemControl


@Factory.register
class ReadoutSystemControl(SystemControl):
    """System control used for readout."""

    name = SystemControlName.READOUT_SYSTEM_CONTROL

    def acquire_result(self) -> Result:
        """Read the result from the vector network analyzer instrument

        Returns:
            Result: Acquired result
        """
        # TODO: Support acquisition from multiple instruments
        results: list[Result] = []
        for instrument in self.instruments:
            result = instrument.acquire_result()
            if result is not None:
                results.append(result)

        if len(results) > 1:
            raise ValueError(
                f"Acquisition from multiple instruments is not supported. Obtained a total of {len(results)} results. "
            )

        return results[0]

    def acquire_qprogram_results(self, acquisitions: list[str], port: str) -> list[Result]:
        """Read the result from the vector network analyzer instrument

        Returns:
            list[Result]: Acquired results in chronological order
        """
        # TODO: Support acquisition from multiple instruments
        total_results: list[list[Result]] = []
        for instrument in self.instruments:
            instrument_results = instrument.acquire_qprogram_results(acquisitions=acquisitions, port=port)
            total_results.append(instrument_results)

        return total_results[0]

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        for instrument in self.instruments:
            if isinstance(instrument, AWGAnalogDigitalConverter):
                return instrument.acquisition_delay_time
        raise ValueError(f"The system control {self.name.value} doesn't have an AWG instrument.")
