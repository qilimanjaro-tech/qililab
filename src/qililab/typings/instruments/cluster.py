"""Class Pulsar"""
import qblox_instruments

from qililab.typings.instruments.device import Device


class Cluster(qblox_instruments.Cluster, Device):  # pylint: disable=abstract-method
    """Typing class of the Cluster class defined by Qblox."""
