"""Class QcmQrm"""
from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm as Driver_QcmQrm

from qililab.typings.instruments.device import Device


class QcmQrm(Driver_QcmQrm, Device):
    """Typing class of the QcmQrm class defined by Qblox."""
