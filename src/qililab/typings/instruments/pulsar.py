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

"""Class Pulsar"""
import qblox_instruments

from qililab.typings.instruments.device import Device


class Pulsar(qblox_instruments.Pulsar, Device):  # pylint: disable=abstract-method
    """Typing class of the Pulsar class defined by Qblox."""

    def module_type(self) -> qblox_instruments.InstrumentType:
        """return the module type"""
        return super().instrument_type()
