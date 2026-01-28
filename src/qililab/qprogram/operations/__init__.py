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

from qilisdk.qprogram.operations import Measure as SdkMeasure
from qilisdk.qprogram.operations import Operation, ResetPhase, SetFrequency, SetPhase, Sync, Wait
from qilisdk.qprogram.operations import Play as SdkPlay

from .acquire import Acquire, AcquireWithCalibratedWeights
from .execute_qprogram import ExecuteQProgram
from .get_parameter import GetParameter
from .measure import (
    Measure,
    MeasureWithCalibratedWaveform,
    MeasureWithCalibratedWaveformWeights,
    MeasureWithCalibratedWeights,
)
from .measure_reset import MeasureReset, MeasureResetCalibrated
from .play import Play, PlayWithCalibratedWaveform
from .set_crosstalk import SetCrosstalk
from .set_gain import SetGain
from .set_markers import SetMarkers
from .set_offset import SetOffset
from .set_parameter import SetParameter
from .set_trigger import SetTrigger
from .wait_trigger import WaitTrigger

__all__ = [
    "Acquire",
    "AcquireWithCalibratedWeights",
    "ExecuteQProgram",
    "GetParameter",
    "Measure",
    "MeasureReset",
    "MeasureResetCalibrated",
    "MeasureWithCalibratedWaveform",
    "MeasureWithCalibratedWaveformWeights",
    "MeasureWithCalibratedWeights",
    "Operation",
    "Play",
    "PlayWithCalibratedWaveform",
    "ResetPhase",
    "SdkMeasure",
    "SdkPlay",
    "SetCrosstalk",
    "SetFrequency",
    "SetGain",
    "SetMarkers",
    "SetOffset",
    "SetParameter",
    "SetPhase",
    "SetTrigger",
    "Sync",
    "Wait",
    "WaitTrigger",
]
