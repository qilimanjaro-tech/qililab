import os
from pathlib import Path

from qililab import build_platform
from qililab.circuit import Circuit
from qililab.circuit.converters import QiliQasmConverter
from qililab.circuit.operations import (
    R180,
    GaussianPulse,
    Measure,
    Operation,
    PulseOperation,
    Reset,
    Rxy,
    Wait,
    X,
)
from qililab.execution.circuit_transpiler import CircuitTranspiler
from qililab.settings import RuncardSchema
from qililab.typings.enums import OperationTimingsCalculationMethod

fname = os.path.abspath("")
os.environ["RUNCARDS"] = str(Path(fname) / "runcards")
runcard_name = "internal_circuit"
platform = build_platform(name=runcard_name)

op = Operation()
pulse = PulseOperation(amplitude=1.0, duration=100)

circuit = Circuit(2)
circuit.add((0, 1), X())
circuit.add(0, Wait(t=100))
circuit.add(0, X())
circuit.add((0, 1), Measure())

print(circuit.get_operation_layers())
print(circuit.get_operation_layers(OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE))

# print circuit in the usual way
circuit.print()

# draw circuit's graph, which in essense is a time dependency graph of operations
image = circuit.draw()
image.show()

transpiler = CircuitTranspiler(circuit, platform.settings)
transpiler.calculate_timings()

# print circuit in the usual way
circuit.print()

# draw circuit's graph, which in essense is a time dependency graph of operations
image = circuit.draw()
image.show()

print(f"Depth: {circuit.depth}")

# or save to file
# circuit.draw(filename='circuit.png')

# Convert to QiliQASM
qasm = QiliQasmConverter.circuit_to_qasm(circuit)
print(qasm)

# Parse from QiliQASM
parsed_circuit = QiliQasmConverter.qasm_to_circuit(qasm)
image = parsed_circuit.draw()
image.show()
