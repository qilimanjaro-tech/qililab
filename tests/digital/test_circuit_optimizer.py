import numpy as np
from qibo import Circuit, gates

from qililab.digital.circuit_optimizer import CircuitOptimizer
from qililab.digital.native_gates import Drag


class TestCircuitOptimizer:
    """Tests for the circuit optimizer class."""

    def test_run_gate_cancelation(self):
        """Test run gate cancelation."""
        # Create a circuit with two gates that cancel each other.
        circuit = Circuit(5)

        # pairs that cancels:
        circuit.add(gates.H(0))
        circuit.add(gates.H(0))

        # From here only the X(4) will cancel with the X(4) at the end.
        circuit.add(gates.CNOT(2,3)) # 1
        circuit.add(gates.X(4))
        circuit.add(gates.H(3)) # 2

        # The 0-1 and 1-4 CNOTs shold cancel each other.
        circuit.add(gates.CNOT(1,4))
        circuit.add(gates.CNOT(0,1))
        circuit.add(Drag(3, theta=2*np.pi, phase=np.pi)) # 3
        circuit.add(gates.CNOT(0,1))
        circuit.add(gates.CNOT(1,4))

        circuit.add(gates.H(3)) # 4
        circuit.add(gates.X(4))
        circuit.add(gates.CNOT(2,3)) # 5


        # Optimize the circuit.
        optimizer = CircuitOptimizer(None)
        optimized_circuit = optimizer.run_gate_cancellations(circuit)

        # Check that the circuit is optimized
        assert len(optimized_circuit.queue) == 5
        # Check name attribute:
        assert [gate.name for gate in optimized_circuit.queue] == ["cx", "h", "drag", "h", "cx"]
        # CHeck the type of the gates:
        assert [type(gate).__name__ for gate in optimized_circuit.queue] == ["CNOT", "H", "Drag", "H", "CNOT"]
        # Assert the initial arguments:
        assert [gate.init_args for gate in optimized_circuit.queue] == [[2,3], [3], [3], [3], [2,3]]
        assert [gate.init_kwargs for gate in optimized_circuit.queue] == [{}, {}, {"theta": 2*np.pi, "phase": np.pi, "trainable": True}, {}, {}]
