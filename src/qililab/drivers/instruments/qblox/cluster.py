from typing import Dict, Union

from qblox_instruments.qcodes_drivers import Cluster as QcodesCluster
from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm as QcodesQcmQrm
from qcodes import Instrument
from qcodes.instrument import DelegateParameter
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from qililab.drivers import parameters
from qililab.drivers.interfaces import Attenuator, LocalOscillator

from .sequencer import AWGSequencer


class Cluster(QcodesCluster):
    """Qililab's driver for QBlox-instruments Cluster"""

    def __init__(self, name: str, address: str | None = None, **kwargs):
        """Initialise the instrument.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        super().__init__(name, identifier=address, **kwargs)

        # Add qcm-qrm's to the cluster
        self.submodules: Dict[str, Union[InstrumentModule, ChannelTuple]] = {}  # resetting superclass submodules
        self.instrument_modules: Dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: Dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        # registering only the slots specified in the dummy config if that is the case
        if "dummy_cfg" in kwargs:
            slot_ids = list(kwargs["dummy_cfg"].keys())
        else:
            slot_ids = [i for i in range(1, self._num_slots + 1)]

        for slot_idx in slot_ids:
            module = QcmQrm(self, "module{}".format(slot_idx), slot_idx)
            self.add_submodule("module{}".format(slot_idx), module)


class QcmQrm(QcodesQcmQrm):
    """Qililab's driver for QBlox-instruments QcmQrm"""

    def __init__(self, parent: Instrument, name: str, slot_idx: int, **kwargs):
        """Initialise the instrument.

        Args:
            parent (Instrument): Instrument´s parent
            name (str): Name of the instrument
            slot_idx (int): Index of the slot
        """
        super().__init__(parent, name, slot_idx)

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

        # Add sequencers
        self.submodules: dict[str, Union[InstrumentModule, ChannelTuple]] = {}  # resetting superclass submodules
        self.instrument_modules: Dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: Dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)


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

    def on(self):
        self.device.set("status", True)

    def off(self):
        self.device.set("status", False)


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
