from abc import ABC

from boilerplate.config import logger


class BoilerPlate(ABC):
    """Example boiler plate class

    Args:
        ABC (ABC): Helper class that provides a standard way to create an ABC using inheritance.
    """

    def __init__(self):
        """Initialize the BoilerPlate"""
        logger.info("Initializing BoilerPlate library class")
