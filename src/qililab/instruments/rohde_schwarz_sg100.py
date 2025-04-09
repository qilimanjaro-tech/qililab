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

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument import Instrument
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.runcard.runcard_instruments import RohdeSchwarzSG100RuncardInstrument, RuncardInstrument
from qililab.settings.instruments.rohde_schwarz_sg100_settings import RohdeSchwarzSG100Settings
from qililab.typings.instruments.rohde_schwarz import RohdeSchwarzSGS100ADevice


@InstrumentFactory.register(InstrumentType.ROHDE_SCHWARZ_SG100)
class RohdeSchwarzSG100(Instrument[RohdeSchwarzSGS100ADevice, RohdeSchwarzSG100Settings]):
    def __init__(self, settings: RohdeSchwarzSG100Settings | None = None):
        super().__init__(settings=settings)

        self.add_parameter(
            name="power",
            settings_field="power",
            get_device_value=self._get_power,
            set_device_value=self._set_power
        )
        self.add_parameter(
            name="frequency",
            settings_field="frequency",
            get_device_value=self._get_frequency,
            set_device_value=self._set_frequency
        )
        self.add_parameter(
            name="rf_on",
            settings_field="rf_on",
            get_device_value=self._get_rf_on,
            set_device_value=self._set_rf_on
        )

    @classmethod
    def get_default_settings(cls) -> RohdeSchwarzSG100Settings:
        return RohdeSchwarzSG100Settings(alias="sg100", power=0.0, frequency=1e9, rf_on=False)

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

    def _get_power(self):
        return self.device.power()

    def _set_power(self, value: float):
        self.device.power(value)

    def _get_frequency(self):
        return self.device.frequency()

    def _set_frequency(self, value: float):
        self.device.frequency(value)

    def _get_rf_on(self):
        status = self.device.status()
        return True if status == "on" else False

    def _set_rf_on(self, value):
        if value:
            self.device.on()
        else:
            self.device.off()

    def to_runcard(self) -> RuncardInstrument:
        return RohdeSchwarzSG100RuncardInstrument(settings=self.settings)
