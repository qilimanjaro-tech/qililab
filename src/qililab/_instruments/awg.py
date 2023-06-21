import numpy as np
from qcodes import Instrument
from qililab.pulse import PulseBusSchedule
from typing import Any

class AWG(Instrument):
    """
    Interface for AWG sequencer instrument types.
    """ 
    def set(self, param_name:str, value:Any):
        """Set parameter on the instrument.
        Args:
            param (str): Parameter's name.
            value (float): Parameter's value
        """
        self.add_parameter(param_name, vals=value)

    
    def get(self, param_name:str):
        """Return value associated to a parameter on the instrument.
        Args:
            param (str): Parameter's name.
        Returns:
            value (float): Parameter's value
        """
        return self.get(param_name)

    def execute(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int):
        ...
