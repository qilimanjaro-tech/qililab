import os
from pathlib import Path

from qililab import build_platform
from qililab.circuit import Circuit
from qililab.circuit.converters import QiliQasmConverter
from qililab.circuit.operations import (
    R180,
    Barrier,
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

# print circuit in the usual way
circuit.print()

# draw circuit's graph, which in essense is a time dependency graph of operations
image = circuit.draw(filename="ir_0.png")
# image.show()

transpiler = CircuitTranspiler(circuit, platform.settings)
transpiler.calculate_timings()
image = circuit.draw(filename="ir_1.png")
# image.show()

transpiler.translate_to_pulse_operations()
image = circuit.draw(filename="ir_2.png")
# image.show()

# print circuit in the usual way
# circuit.print()

print(f"Depth: {circuit.depth}")

# or save to file
# circuit.draw(filename='circuit.png')

# Convert to QiliQASM
# qasm = QiliQasmConverter.to_qasm(circuit)
# print(qasm)

# Parse from QiliQASM
# parsed_circuit = QiliQasmConverter.from_qasm(qasm)
# image = parsed_circuit.draw()
# image.show()
