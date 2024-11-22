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

from typing import Any, Callable, Dict

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument2 import Instrument2
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.runcard.runcard_instruments import RohdeSchwarzSG100RuncardInstrument, RuncardInstrument
from qililab.settings.instruments.rohde_schwarz_sg100_settings import RohdeSchwarzSG100Settings
from qililab.typings.enums import Parameter
from qililab.typings.instruments.rohde_schwarz import RohdeSchwarzSGS100ADevice


@InstrumentFactory.register(InstrumentType.ROHDE_SCHWARZ_SG100)
class RohdeSchwarzSG100(Instrument2[RohdeSchwarzSGS100ADevice, RohdeSchwarzSG100Settings, None, None]):
    @classmethod
    def get_default_settings(cls) -> RohdeSchwarzSG100Settings:
        return RohdeSchwarzSG100Settings(alias="sg100", power=0.0, frequency=1e9, rf_on=False)

    @classmethod
    def parameter_to_instrument_settings(cls) -> Dict[Parameter, str]:
        return {
            Parameter.POWER: "power",
            Parameter.LO_FREQUENCY: "frequency",
            Parameter.RF_ON: "rf_on",
        }

    @classmethod
    def parameter_to_channel_settings(cls) -> Dict[Parameter, str]:
        return {}

    def get_channel_settings(self, channel: None):
        raise NotImplementedError("SG100 does not support channels.")

    def parameter_to_device_operation(self) -> Dict[Parameter, Callable[[Any], None]]:
        return {
            Parameter.POWER: self._on_power_changed,
            Parameter.LO_FREQUENCY: self._on_frequency_changed,
            Parameter.RF_ON: self._on_rf_on_changed,
        }

    def _on_power_changed(self, value: float):
        self.device.power(value)

    def _on_frequency_changed(self, value: float):
        self.device.frequency(value)

    def _on_rf_on_changed(self, value):
        if value:
            self.device.on()
        else:
            self.device.off()

    def to_runcard(self) -> RuncardInstrument:
        return RohdeSchwarzSG100RuncardInstrument(settings=self.settings)

    @check_device_initialized
    def turn_on(self):
        raise NotImplementedError

    @check_device_initialized
    def turn_off(self):
        raise NotImplementedError

    @check_device_initialized
    def reset(self):
        raise NotImplementedError

    @check_device_initialized
    def initial_setup(self):
        raise NotImplementedError
