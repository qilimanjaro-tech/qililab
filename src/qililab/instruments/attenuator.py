"""SignalGenerator class."""
from abc import ABC, abstractmethod


class Attenuator(ABC):
    """_summary_

    Args:
        ABC (_type_): _description_
    """

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def set(self, attenuation: int):
        """set method for the attenuator parameters"""
        raise NotImplementedError("Subclasses must implement set_attenuation.")

    @abstractmethod
    def get(self):
        """get method to check status of attenuator"""
        raise NotImplementedError("Subclasses must implement get_attenuation.")
