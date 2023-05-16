"""FactoryElement class"""
from enum import Enum
from typing import Protocol


class FactoryElement(Protocol):
    """Class FactoryElement"""

    name: Enum
