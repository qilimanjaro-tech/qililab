"""Class QcmQrm"""
import qblox_instruments

from qililab.typings.instruments.device import Device


class QcmQrm(qblox_instruments.qcodes_drivers.qcm_qrm.QcmQrm, Device):
    """Typing class of the QcmQrm class defined by Qblox."""
