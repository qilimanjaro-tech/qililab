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

"""Qblox Pulsar Controller class"""
from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentController, InstrumentControllerSettings
from qililab.instruments.qblox.qblox_qcm import QbloxQCM
from qililab.instruments.qblox.qblox_qrm import QbloxQRM
from qililab.typings.enums import InstrumentTypeName, Parameter, ReferenceClock
from qililab.typings.instruments.cluster import Cluster
from qililab.typings.instruments.pulsar import Pulsar


class QbloxController(InstrumentController):
    """Qblox Controller class.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        settings (QbloxControllerSettings): Settings of the Qblox Pulser Instrument Controller.
    """

    @dataclass
    class QbloxControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Qblox Pulsar Controller."""

        reference_clock: ReferenceClock

    settings: QbloxControllerSettings
    device: Pulsar | Cluster
    modules: Sequence[QbloxQCM | QbloxQRM]

    @InstrumentController.CheckConnected
    def initial_setup(self):
        """Initial setup"""
        self._set_reference_source()
        super().initial_setup()

    @InstrumentController.CheckConnected
    @abstractmethod
    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""

    @property
    def reference_clock(self):
        """Qblox 'reference_clock' property.

        Returns:
            ReferenceClock: settings.reference_clock.
        """
        return self.settings.reference_clock

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, QbloxQCM) and not isinstance(module, QbloxQRM):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument are {InstrumentTypeName.QBLOX_QCM} "
                    + f"and {InstrumentTypeName.QBLOX_QRM}."
                )

    def to_dict(self):
        """Return a dict representation of the Qblox controller class."""
        return super().to_dict() | {
            Parameter.REFERENCE_CLOCK.value: self.reference_clock.value,
        }
