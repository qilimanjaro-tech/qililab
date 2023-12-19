"""Tests for the Qblox Module class."""
import copy

import numpy as np
import pytest
from qpysequence.program import Loop, Register
from qpysequence.utils.constants import AWG_MAX_GAIN
from qpysequence.weights import Weights

from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from tests.data import Galadriel



class TestQbloxModule:
    """Unit tests checking the QbloxQCM attributes and methods"""


# test self.sequencer

"""
    def test_upload_method(self, qcm, pulse_bus_schedule):
        
        qcm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=100, num_bins=1)
        qcm.upload(port=pulse_bus_schedule.port)
        qcm.device.sequencer0.sequence.assert_called_once()
        qcm.device.sequencer0.sync_en.assert_called_once_with(True)
   


    def test_upload_method(self, qrm, pulse_bus_schedule):
   
        pulse_bus_schedule.port = "feedline_input"
        qrm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=100, num_bins=1)
        qrm.upload(port=pulse_bus_schedule.port)
        qrm.device.sequencers[0].sync_en.assert_called_once_with(True)
        qrm.device.sequencers[1].sequence.assert_not_called()
        # TODO: test that sequence from compule is added to qrm sequences
"""