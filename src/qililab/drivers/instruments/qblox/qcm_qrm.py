from typing import Union

from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm as QcodesQcmQrm
from qcodes import Instrument
from qcodes.instrument import DelegateParameter
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from qililab.drivers import AWGSequencer, parameters
from qililab.drivers.interfaces import LocalOscillator


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
            lo_channels = 1 if super().is_qrm_type else 2
            for channel in range(lo_channels):
                lo = QcmQrmRfLo(name=f"{name}_lo{channel}", parent=self, channel=channel)
                self.add_submodule(f"{name}_lo{channel}", lo)

        # Add sequencers
        self.submodules: dict[str, Union[InstrumentModule, ChannelTuple]] = {}
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)


class QcmQrmRfLo(InstrumentModule, LocalOscillator):
    """LO driver for the QCM / QRM - RF instrument
    Set and get methods from InstrumentModule override LocalOscillator's
    """

    def __init__(self, name: str, parent: QcmQrm, channel: int = 0, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.device = parent

        # get the name of the parameter for the lo frequency
        lo_frequency = parameters.drivers.lo
        if parent.is_qrm_type:  # qrm-rf has only one lo channel
            self.add_parameter(
                lo_frequency,
                label="Delegated parameter for qrm local oscillator frequency",
                source=self.parameters["out0_in0_lo_freq"],
                parameter_class=DelegateParameter,
            )
            self.add_parameter(
                "status",
                label="Delegated parameter device status",
                source=self.parameters["out0_in0_lo_en"],
                parameter_class=DelegateParameter,
            )

        else:  # qcm-rf
            self.add_parameter(
                lo_frequency,
                label="Delegated parameter for qcm local oscillator frequency",
                source=self.parameters[f"out{channel}_lo_freq"],
                parameter_class=DelegateParameter,
            )
            self.add_parameter(
                "status",
                label="Delegated parameter device status",
                source=self.parameters[f"out{channel}_lo_en"],
                parameter_class=DelegateParameter,
            )

    def on(self):
        self.device.set("status", True)

    def off(self):
        self.device.set("status", False)
