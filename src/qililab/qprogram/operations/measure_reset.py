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

from typing import Any

from qililab.constants import QBLOXCONSTANTS
from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQWaveform
from qililab.yaml import yaml


@yaml.register_class
class MeasureReset(Operation):
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
        self.padding_after_measure: int = padding_after_measure

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore the operation during deserialization, with ``padding_after_measure`` set to its default when the YAML
        was written before it existed: ``ruamel`` builds the object with ``cls.__new__`` and never calls ``__init__``.

        Args:
            state (dict[str, Any]): The attribute mapping reconstructed from the document.
        """
        self.__dict__.update({"padding_after_measure": QBLOXCONSTANTS.WAIT_TRIGGER_NETWORK_INTERMODULES, **state})


@yaml.register_class
class MeasureResetCalibrated(Operation):
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
        self.padding_after_measure: int = padding_after_measure

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore the operation during deserialization, with ``padding_after_measure`` set to its default when the YAML
        was written before it existed: ``ruamel`` builds the object with ``cls.__new__`` and never calls ``__init__``.

        Args:
            state (dict[str, Any]): The attribute mapping reconstructed from the document.
        """
        self.__dict__.update({"padding_after_measure": QBLOXCONSTANTS.WAIT_TRIGGER_NETWORK_INTERMODULES, **state})
