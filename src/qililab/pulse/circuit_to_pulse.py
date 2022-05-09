"""CircuitToPulse class"""
from qibo.core.circuit import Circuit


def circuit_to_pulse(circuit: Circuit):
    """Translate a Qibo circuit to a list of PulseSequences."""
