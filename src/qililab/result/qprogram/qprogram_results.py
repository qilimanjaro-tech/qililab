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

"""MeasurementResult class."""
from qililab.result.qprogram.measurement_result import MeasurementResult
from qililab.utils.dict_serializable import DictSerializable


class QProgramResults(DictSerializable):
    """Results from a single execution of QProgram."""

    def __init__(self) -> None:
        self.results: dict[str, list[MeasurementResult]] = {}

    def append_result(self, bus: str, result: MeasurementResult):
        """Append a measurement result to bus's results list.

        Args:
            bus (str): The bus alias
            result (MeasurementResult): The measurement result to append.
        """
        if bus not in self.results:
            self.results[bus] = []
        self.results[bus].append(result)
