import numpy as np

from qcodes import Instrument
from qililab.pulse import PulseBusSchedule, PulseShape
from qpysequence.sequence import Sequence as QpySequence
from qpysequence.waveforms import Waveforms

class AWG:
    """
    Interface for AWG instrument types.
    """
    def set(self, param:str, value:float):
        """Set parameter on the instrument.
        Args:
            param (str): Parameter's name.
            value (float): Parameter's value
        """

    
    def get(self, param:str):
        """Return value associated to a parameter on the instrument.
        Args:
            param (str): Parameter's name.
        Returns:
            value (float): Parameter's value
        """


    def execute(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int):
        """Execute a PulseBusSchedule on the instrument.
        Args:
            pulse_bus_schedule (PulseBusSchedule): PulseBusSchedule to be translated into QASM program and executed.
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins
        """
