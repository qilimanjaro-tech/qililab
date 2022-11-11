"""KeySight Vector Network Analyzer E5080B class."""
from dataclasses import dataclass

from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.typings.enums import InstrumentName
from qililab.typings.instruments.keysight_e5080b import E5080BDriver


@InstrumentFactory.register
class E5080B(VectorNetworkAnalyzer):
    """KeySight Vector Network Analyzer E5080B"""

    name = InstrumentName.KEYSIGHT_E5080B
    device: E5080BDriver

    @dataclass
    class E5080BSettings(VectorNetworkAnalyzer.VectorNetworkAnalyzerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer"""

    settings: E5080BSettings


    def setup(self):
        self.device.send_command(command="*IDN?")
        self.device.read()
        print("[instrument.keysight.e5080b_vna]")
