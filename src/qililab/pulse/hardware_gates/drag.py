"""Drag gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.transpiler import Drag as Drag_gate
from qililab.typings import GateName


@HardwareGateFactory.register
class Drag(HardwareGate):  # pylint: disable=invalid-name
    """Drag pulse gate.

    This is a gate representation of the Drag pulse as a native gate.
    """

    name = GateName.Drag
    class_type = Drag_gate

    @classmethod
    def translate(
        cls,
        gate: Drag_gate,
        master_amplitude_gate: float,
        master_duration_gate: int,
    ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        qubit = gate.target_qubits[0]
        return cls.parameters(
            qubits=qubit,
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
