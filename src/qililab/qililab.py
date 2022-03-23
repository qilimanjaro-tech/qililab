from abc import ABC

from qililab.config import logger


class Qililab(ABC):
    """Example class

    Args:
        ABC (ABC): Helper class that provides a standard way to create an ABC using inheritance.
    """

    def __init__(self):
        """Initialize the Qililab"""
        logger.info("Initializing Qililab library class")
