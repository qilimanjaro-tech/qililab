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

from qililab.constants import QBLOXCONSTANTS
from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQWaveform
from qililab.yaml import yaml


@yaml.register_class
class MeasureReset(Operation):
    # Used when loading a YAML written before padding_after_measure existed: ruamel builds the object without calling
    # __init__, so the missing attribute falls back to this class attribute.
    padding_after_measure: int = QBLOXCONSTANTS.WAIT_TRIGGER_NETWORK_INTERMODULES

    def __init__(
        self,
        bus: str,
        waveform: IQWaveform,
        weights: IQWaveform,
        control_bus: str,
        reset_pulse: IQWaveform,
        trigger_address: int = 1,
        save_adc: bool = False,
        padding_after_measure: int = QBLOXCONSTANTS.WAIT_TRIGGER_NETWORK_INTERMODULES,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: IQWaveform = waveform
        self.weights: IQWaveform = weights
        self.control_bus: str = control_bus
        self.reset_pulse: IQWaveform = reset_pulse
        self.trigger_address: int = trigger_address
        self.save_adc: bool = save_adc
        self.padding_after_measure = padding_after_measure


@yaml.register_class
class MeasureResetCalibrated(Operation):
    # Used when loading a YAML written before padding_after_measure existed: ruamel builds the object without calling
    # __init__, so the missing attribute falls back to this class attribute.
    padding_after_measure: int = QBLOXCONSTANTS.WAIT_TRIGGER_NETWORK_INTERMODULES

    def __init__(
        self,
        bus: str,
        waveform: str,
        weights: str,
        control_bus: str,
        reset_pulse: str,
        trigger_address: int = 1,
        save_adc: bool = False,
        padding_after_measure: int = QBLOXCONSTANTS.WAIT_TRIGGER_NETWORK_INTERMODULES,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.weights: str = weights
        self.control_bus: str = control_bus
        self.reset_pulse: str = reset_pulse
        self.trigger_address: int = trigger_address
        self.save_adc: bool = save_adc
        self.padding_after_measure = padding_after_measure
