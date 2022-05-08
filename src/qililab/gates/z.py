from qibo.gates import Z as ZQibo

from qililab.gates.hardware_gate import HardwareGate


class Z(HardwareGate, ZQibo):  # pylint: disable=invalid-name
    """Z gate

    Args:
        q (int): Index of the qubit to which the gate is applied.
    """

    def to_sequence(self, sequence: object):
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise NotImplementedError
