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

from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox_qcm import QbloxQCM
from qililab.runcard.runcard_instruments import QbloxQCMRFRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxQCMRFSettings, QbloxSequencerSettings


@InstrumentFactory.register(InstrumentType.QBLOX_QCM_RF)
class QbloxQCMRF(QbloxQCM):
    settings: QbloxQCMRFSettings

    @classmethod
    def get_default_settings(cls) -> QbloxQCMRFSettings:
        return QbloxQCMRFSettings(alias="qcm-rf", sequencers=[QbloxSequencerSettings(id=index) for index in range(6)])

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQCMRFRuncardInstrument(settings=self.settings)

    def _map_output_connections(self):
        """Disable all connections and map sequencer paths with output channels."""
        self.device.disconnect_outputs()

        for sequencer in self.settings.sequencers:
            operations = {
                0: self.device.sequencers[sequencer.id].connect_out0,
                1: self.device.sequencers[sequencer.id].connect_out1,
            }
            output = sequencer.outputs[0]
            operations[output]("IQ")
