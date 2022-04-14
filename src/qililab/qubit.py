"""Qubit class"""
from qililab.settings import QubitCalibrationSettings


class Qubit:
    """Qubit class"""

    def __init__(self, settings: dict):
        self.settings = QubitCalibrationSettings(**settings)
