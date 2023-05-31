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
    If no t_phi is defined, allows for other standard pulse shapes
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
        if "t_phi" in cz_params.shape:  # allow to choose different shapes for the pulse
            cz_duration = 2 * cz_params.duration + 2 + cz_params.shape["t_phi"]
        else:
            cz_duration = cz_params.duration
        return cls.HardwareGateSettings(
            amplitude=cz_params.amplitude, phase=cz_params.phase, duration=cz_duration, shape=cz_params.shape
        )
