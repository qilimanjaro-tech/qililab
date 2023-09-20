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

"""Single Instrument Controller class"""
from qililab.instrument_controllers.instrument_controller import InstrumentController


class SingleInstrumentController(InstrumentController):
    """Controller device that only controls one single instrument.

    Args:
        number_available_modules (int): Number of modules available in the Instrument Controller.
                                        In this case, there is only one instrument available.
    """

    number_available_modules: int = 1

    def _set_device_to_all_modules(self):
        """Sets the initialized device to the attached module.
        For a SingleInstrumentController, by default,
        the same controller device driver is set to the Instrument.
        """
        self.modules[0].device = self.device
