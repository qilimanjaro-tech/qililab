"""KeySight Vector Network Analyzer E5080B class."""
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.typings.enums import InstrumentName


@InstrumentFactory.register
class E5080B(VectorNetworkAnalyzer):
    """KeySight Vector Network Analyzer E5080B"""

    name = InstrumentName.KEYSIGHT_E5080B
