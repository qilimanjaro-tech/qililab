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

"""The operations qililab adds to qprogram's, and the operations of an ``Experiment``."""

from .disable_autosync import DisableAutosync
from .execute_qprogram import ExecuteQProgram
from .get_parameter import GetParameter
from .measure_reset import MeasureReset
from .play import QbloxPlay
from .set_crosstalk import SetCrosstalk
from .set_parameter import SetParameter

__all__ = [
    "DisableAutosync",
    "ExecuteQProgram",
    "GetParameter",
    "MeasureReset",
    "QbloxPlay",
    "SetCrosstalk",
    "SetParameter",
]
