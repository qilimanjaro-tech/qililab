"""Class KeySight E5080B"""
from dataclasses import dataclass

from .vector_network_analyzer import VectorNetworkAnalyzerDriver


@dataclass
class E5080BDriver(VectorNetworkAnalyzerDriver):
    """Typing class of the KeySight E5080B PyVisa driver."""
