import os
from pathlib import Path

from qililab import Circuit, Measure, QiliQasmConverter, Wait, X, build_platform
from qililab.circuit.circuit_transpiler import CircuitTranspiler
from qililab.settings import RuncardSchema
from qililab.typings.enums import OperationTimingsCalculationMethod

fname = os.path.abspath("")
os.environ["RUNCARDS"] = str(Path(fname) / "runcards")
runcard_name = "internal_circuit"
platform = build_platform(name=runcard_name)

circuit = Circuit(2)
circuit.add((0, 1), X())
circuit.add(0, Wait(t=100))
circuit.add(0, X())
circuit.add((0, 1), Measure())
# circuit.add(0, X())
# circuit.add(1, X())
# circuit.add(1, X())
# circuit.add(1, X())
# circuit.add((0, 1), Barrier())
# circuit.add((0, 1), X())

# get layers with two different methods
# print(circuit.get_operation_layers())
# print(circuit.get_operation_layers(OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE))

# print depth of circuit
print(f"Depth: {circuit.depth}")

# print circuit in the usual way
circuit.print()

# draw circuit's graph, which in essense is a time dependency graph of operations
circuit.draw()

# or save to file
# circuit.draw(filename='circuit.png')

# create the transpiler
transpiler = CircuitTranspiler(settings=platform.settings)

# calculate timings
circuit_ir1 = transpiler.calculate_timings(circuit)
circuit_ir1.draw()

# translate operations to pulse operations
circuit_ir2 = transpiler.transpile_to_pulse_operations(circuit_ir1)
circuit_ir2.draw()

# Convert to QiliQASM
qasm = QiliQasmConverter.to_qasm(circuit)
print(qasm)

# Parse from QiliQASM
parsed_circuit = QiliQasmConverter.from_qasm(qasm)
