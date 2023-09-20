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

"""Generic interface for a Digitiser."""
from abc import abstractmethod
from typing import Any

from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class Digitiser(BaseInstrument):
    """Digitiser interface."""

    @abstractmethod
    def get_results(self) -> Any:
        """Get the acquisition results."""
