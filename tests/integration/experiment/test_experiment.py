from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment
from qililab.pulse import Pulse, PulseSequences, ReadoutPulse
from qililab.pulse.pulse_shape import Drag


def test_experiment():
    """Test experiment"""
    pulse_sequence = PulseSequences(delay_between_pulses=0, delay_before_readout=50)
    pulse_sequence.add(Pulse(amplitude=1, phase=0, pulse_shape=Drag(num_sigmas=4, beta=1), duration=50, qubit_ids=[0]))
    pulse_sequence.add(ReadoutPulse(amplitude=1, phase=0, duration=50, qubit_ids=[0]))

    Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=[pulse_sequence])
