"""Class Agilent E5071B"""
from dataclasses import dataclass

from .vector_network_analyzer import VectorNetworkAnalyzerDriver


@dataclass
class E5071BDriver(VectorNetworkAnalyzerDriver):
    """Typing class of the Agilent E5071B PyVisa driver."""
