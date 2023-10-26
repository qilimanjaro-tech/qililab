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

from qcodes.instrument import DelegateParameter
from qcodes.instrument_drivers.rohde_schwarz import RohdeSchwarzSGS100A as QcodesSGS100A

from qililab.drivers import parameters
from qililab.drivers.instruments.instrument_driver_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import LocalOscillator


@InstrumentDriverFactory.register
class RhodeSchwarzSGS100A(QcodesSGS100A, LocalOscillator):
    """Qililab's driver for the SGS100A local oscillator

    QcodesSGS100A: QCoDeS Rohde Schwarz driver for SGS100A
    LocalOscillator: Qililab's local oscillator interface
    """

    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name, address, **kwargs)

        # change the name for frequency
        self.add_parameter(
            parameters.lo.frequency,
            label="Delegated parameter for local oscillator frequency",
            source=self.parameters["frequency"],
            parameter_class=DelegateParameter,
        )

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name
