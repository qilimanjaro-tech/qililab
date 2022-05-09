"""Draw experiment"""
import matplotlib.pyplot as plt

from qililab import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.pulse import Pulse, PulseSequence, ReadoutPulse
from qililab.pulse.pulse_shape import Drag, Gaussian


def load_experiment():
    """Load the platform 'platform_0' from the DB."""
    # Using PLATFORM_MANAGER_DB
    sequence = PulseSequence(delay_between_pulses=10)
    sequence.add(Pulse(amplitude=1, phase=0, duration=50, pulse_shape=Drag(num_sigmas=4, beta=1), qubit_ids=[1]))
    sequence.add(Pulse(amplitude=1, phase=0, duration=50, pulse_shape=Gaussian(num_sigmas=4), qubit_ids=[0]))
    sequence.add(ReadoutPulse(amplitude=1, phase=0, duration=1000, qubit_ids=[1]))
    sequence.add(ReadoutPulse(amplitude=1, phase=0, duration=1000, qubit_ids=[0]))

    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequence=sequence)
    figure = experiment.draw(resolution=0.1)
    figure.show()
    plt.show()


if __name__ == "__main__":
    load_experiment()
