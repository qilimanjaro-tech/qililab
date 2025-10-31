import numpy as np

from .arbitrary import Arbitrary
from .iq_pair import IQPair
from .iq_waveform import IQWaveform


def transform_pi_calibrated_waveform(pi_drag: IQWaveform, theta: float, phase: float) -> IQPair:
    """
    Build (I, Q) envelopes for a microwave rotation Rmw(theta, phase),
    starting from a DRAG waveform calibrated for an X (π) rotation.

    Args:
        drag: IQDrag with parameters (amplitude, duration, num_sigmas, drag_coefficient)
                calibrated to produce a π rotation about +X when phase=0.
        theta: desired rotation angle in radians.
        phase: rotation axis phase in radians (0 -> X, +π/2 -> Y).

    Returns:
        I_env, Q_env: numpy arrays for the rotated-and-scaled envelopes.
    """
    def wrap_to_pi(x):
        return (x + np.pi) % (2 * np.pi) - np.pi

    theta_mod = wrap_to_pi(theta)

    # Push negative theta into a +π phase shift
    if theta_mod < 0:
        theta_mod = -theta_mod
        phase += np.pi

    phase = wrap_to_pi(phase)

    I0 = pi_drag.get_I().envelope()
    Q0 = pi_drag.get_Q().envelope()

    c, s = np.cos(phase), np.sin(phase)
    scale = theta_mod / np.pi  # drag is a π-pulse; scale linearly to θ

    # Phase rotation in the IQ plane followed by θ scaling
    I_env = scale * (I0 * c - Q0 * s)
    Q_env = scale * (I0 * s + Q0 * c)

    return IQPair(Arbitrary(I_env), Arbitrary(Q_env))
