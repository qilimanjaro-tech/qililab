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

from qblox_instruments.qcodes_drivers import Cluster as QcodesCluster
from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm as QcodesQcmQrm
from qcodes import Instrument
from qcodes.instrument import DelegateParameter
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from qililab.drivers import parameters
from qililab.drivers.instruments.instrument_driver_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import Attenuator, BaseInstrument, LocalOscillator

from .sequencer_qcm import SequencerQCM
from .sequencer_qrm import SequencerQRM


@InstrumentDriverFactory.register
class Cluster(QcodesCluster, BaseInstrument):  # pylint: disable=abstract-method
    """Qililab's driver for QBlox-instruments Cluster.

    Args:
        name (str): The name/alias of the cluster.
        address (str): The IP address of the cluster.

    Keyword Args:
        **kwargs: Any additional keyword arguments provided are passed to its `parent class
            <https://qblox-qblox-instruments.readthedocs-hosted.com/en/master/api_reference/cluster.html>`_.
    """

    def __init__(self, name: str, address: str | None = None, **kwargs):
        super().__init__(name, identifier=address, **kwargs)

        # registering only the slots specified in the dummy config if that is the case
        if "dummy_cfg" in kwargs:
            slot_ids = list(kwargs["dummy_cfg"].keys())
        else:
            slot_ids = list(range(1, self._num_slots + 1))

        # Save information about modules actually being present in the cluster
        old_submodules = self.submodules
        submodules_present = [submodule.get("present") for submodule in old_submodules.values()]

        # Add qcm-qrm's to the cluster
        self.submodules: dict[str, InstrumentModule | ChannelTuple] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass channel lists

        for slot_idx in slot_ids:
            if submodules_present[slot_idx - 1]:
                module = QcmQrm(self, f"module{slot_idx}", slot_idx)
                self.add_submodule(f"module{slot_idx}", module)
            else:
                old_module = old_submodules[f"module{slot_idx}"]
                self.add_submodule(f"module{slot_idx}", old_module)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name


class QcmQrm(QcodesQcmQrm, BaseInstrument):
    """Qililab's driver for QBlox-instruments QcmQrm

    Args:
        parent (Instrument): Instrument´s parent
        name (str): Name of the instrument
        slot_idx (int): Index of the slot
    """

    def __init__(self, parent: Instrument, name: str, slot_idx: int):
        super().__init__(parent, name, slot_idx)

        # Add sequencers
        self.submodules: dict[str, InstrumentModule | ChannelTuple] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        sequencer_class = SequencerQCM if self.is_qcm_type else SequencerQRM
        for seq_idx in range(6):
            seq = sequencer_class(parent=self, name=f"sequencer{seq_idx}", seq_idx=seq_idx)  # type: ignore
            self.add_submodule(f"sequencer{seq_idx}", seq)

        # Add RF submodules
        if super().is_rf_type:
            # Add local oscillators
            # We use strings as channels to keep the in/out name and conserve the same
            # logic as for the attenuator or other instruments
            lo_channels = ["out0_in0"] if super().is_qrm_type else ["out0", "out1"]
            for channel in lo_channels:
                lo = QcmQrmRfLo(name=f"{name}_lo_{channel}", parent=self, channel=channel)
                self.add_submodule(f"{name}_lo_{channel}", lo)

            # Add attenuators
            att_channels = ["out0", "in0"] if super().is_qrm_type else ["out0", "out1"]
            for channel in att_channels:
                att = QcmQrmRfAtt(name=f"{name}_attenuator_{channel}", parent=self, channel=channel)
                self.add_submodule(f"{name}_attenuator_{channel}", att)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name


class QcmQrmRfLo(InstrumentModule, LocalOscillator):
    """LO driver for the QCM / QRM - RF instrument
    Set and get methods from InstrumentModule override LocalOscillator's
    """

    def __init__(self, name: str, parent: QcmQrm, channel: str, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.device = parent

        # get the name of the parameter for the lo frequency
        lo_frequency = parameters.lo.frequency
        self.add_parameter(
            lo_frequency,
            label="Delegated parameter for local oscillator frequency",
            source=parent.parameters[f"{channel}_lo_freq"],
            parameter_class=DelegateParameter,
        )
        self.add_parameter(
            "status",
            label="Delegated parameter device status",
            source=parent.parameters[f"{channel}_lo_en"],
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

    def on(self):
        self.set("status", True)

    def off(self):
        self.set("status", False)


class QcmQrmRfAtt(InstrumentModule, Attenuator):
    """Attenuator driver for the QCM / QRM - RF instrument
    Set and get methods from InstrumentModule override Attenuator's
    """

    def __init__(self, name: str, parent: QcmQrm, channel: str, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.device = parent

        # get the name of the parameter for the attenuation
        attenuation = parameters.attenuator.attenuation
        self.add_parameter(
            attenuation,
            label="Delegated parameter for attenuation",
            source=parent.parameters[f"{channel}_att"],
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
