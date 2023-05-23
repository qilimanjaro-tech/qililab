"""CZ gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class CZ(HardwareGate):  # pylint: disable=invalid-name
    """CZ gate.

    CZ / C-Phase gate (2 qubit gate)
    Sends a Sudden Net Zero (SNZ) pulse to the target in CZ(control, target)
    """

    name = GateName.CZ
    class_type = gates.CZ

    @classmethod
    def translate(cls, gate: gates.CZ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.
        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        cz_params = CZ.settings[gate.qubits]
        cz_duration = 2 * cz_params.duration + 2 + cz_params.shape["t_phi"]
        return cls.HardwareGateSettings(
            amplitude=cz_params.amplitude, phase=0, duration=cz_duration, shape=cz_params.shape
        )
