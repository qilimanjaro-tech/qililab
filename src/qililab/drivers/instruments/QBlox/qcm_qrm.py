from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm
from qcodes import Instrument
from qcodes.instrument.channel import InstrumentModule

from qililab.drivers import AWGSequencer
from qililab.drivers.interfaces import LocalOscillator


class QililabQcmQrm(QcmQrm):
    def __init__(self, parent: Instrument, name: str, slot_idx: int, **kwargs):
        super().__init__(parent, name, slot_idx)

        if super().is_rf_type:
            # Add local oscillators
            lo_channels = 1 if super().is_qrm_type else 2
            for channel in range(lo_channels):
                lo = QcmQrmRfLo(name=f"{name}_lo{channel}", parent=self, channel=channel)
                self.add_submodule(f"{name}_lo{channel}", lo)

        # Add sequencers
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)


class QcmQrmRfLo(InstrumentModule, LocalOscillator):
    """LO driver for the QCM / QRM - RF instrument
    Set and get methods from InstrumentModule override LocalOscillator's
    """

    def __init__(self, name: str, parent: QililabQcmQrm, channel: int = 0, **kwargs):
        super().__init__(parent, name, **kwargs)
        self.device = parent

        # TODO: add typings?
        if parent.is_qrm_type:  # qrm-rf has only one lo channel
            self.parameters = {"lo_freq": parent.parameters["out0_in0_lo_freq"]}
            self.parameters = {"status": parent.parameters["out0_in0_lo_en"]}

        else:  # qcm-rf
            self.parameters = {"lo_freq": parent.parameters[f"out{channel}_lo_freq"]}
            self.parameters = {"status": parent.parameters[f"out{channel}_lo_en"]}

    def on(self):
        self.device.set("status", True)

    def off(self):
        self.device.set("status", False)
