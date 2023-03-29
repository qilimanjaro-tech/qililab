"""Agilent Vector Network Analyzer E5071B class."""
from dataclasses import dataclass

from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.typings.enums import InstrumentName
from qililab.typings.instruments.agilent_e5071b import E5071BDriver


@InstrumentFactory.register
class E5071B(VectorNetworkAnalyzer):
    """Agilent Vector Network Analyzer E5071B"""

    name = InstrumentName.AGILENT_E5071B
    device: E5071BDriver

    @dataclass
    class E5071BSettings(VectorNetworkAnalyzer.VectorNetworkAnalyzerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer"""

    settings: E5071BSettings

    def initial_setup(self):
        """Set initial instrument settings."""
