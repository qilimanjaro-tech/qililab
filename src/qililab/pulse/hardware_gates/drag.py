"""Drag gate"""
import numpy as np

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.transpiler import Drag as Drag_gate
from qililab.typings import GateName


@HardwareGateFactory.register
class Drag(HardwareGate):
    """Drag pulse gate.

    This is a gate representation of the Drag pulse as a native gate.
    """

    name = GateName.Drag
    class_type = Drag_gate

    @classmethod
    def translate(cls, gate: Drag_gate) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        qubit = gate.target_qubits[0]
        params = cls.settings[qubit]
        amplitude = params.amplitude * gate.parameters[0] / np.pi
        phase = gate.parameters[1]
        return cls.HardwareGateSettings(amplitude=amplitude, phase=phase, duration=params.duration, shape=params.shape)
