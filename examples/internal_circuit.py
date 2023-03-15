from qililab.circuit import Circuit
from qililab.circuit.converters import QiliQasmConverter
from qililab.circuit.operations import R180, GaussianPulse, Measure, Reset, Rxy, Wait, X

circuit = Circuit(3)
circuit.add(0, Rxy(theta=0, phi=90))
circuit.add(0, Rxy(theta=0, phi=45))
circuit.add(1, R180(phi=0))
circuit.add((0, 1), Wait(t=400))
circuit.add((0, 2), X())
circuit.add((0, 1, 2), Measure())
circuit.add((0, 1, 2), Reset())
circuit.add(0, GaussianPulse(amplitude=1, duration=40, sigma=0.2))
circuit.add(1, X())
circuit.add(2, X())

print(f"Depth: {circuit.depth}")

# print circuit in the usual way
circuit.print()

# draw circuit's graph, which in essense is a time dependency graph of operations
image = circuit.draw()
image.show()

# or save to file
# circuit.draw(filename='circuit.png')

# Convert to QiliQASM
qasm = QiliQasmConverter.circuit_to_qasm(circuit)
print(qasm)

# Parse from QiliQASM
parsed_circuit = QiliQasmConverter.qasm_to_circuit(qasm)
image = parsed_circuit.draw()
image.show()
