import os
from pathlib import Path

from qililab import Barrier, Circuit, Measure, QiliQasmConverter, Reset, SquarePulse, Wait, X, build_platform
from qililab.circuit.circuit_transpiler import CircuitTranspiler
from qililab.circuit.operations.pulse_operations.gaussian import GaussianPulse
from qililab.settings import RuncardSchema
from qililab.typings.enums import OperationTimingsCalculationMethod

fname = os.path.abspath("")
os.environ["RUNCARDS"] = str(Path(fname) / "runcards")
runcard_name = "internal_circuit"
platform = build_platform(name=runcard_name)

circuit = Circuit(2)
circuit.add(0, X())
circuit.add(0, Wait(t=100))
circuit.add(0, X())
circuit.add(1, X())
circuit.add((0, 1), Barrier())
circuit.add(0, X())
circuit.add(0, GaussianPulse(amplitude=1.0, duration=10, phase=0, frequency=8e9, sigma=1))
circuit.add(1, X())
circuit.add((0, 1), Measure())

# print depth of circuit
print(f"Depth: {circuit.depth}")

# print circuit in the usual way
circuit.print()

# draw circuit's graph, which in essense is a time dependency graph of operations
circuit.draw()

# or save to file
# circuit.draw(filename='circuit.png')

# create the transpiler
transpiler = CircuitTranspiler(settings=platform.settings, chip=platform.chip)

# calculate timings
circuit_ir1 = transpiler.calculate_timings(circuit)
circuit_ir1.draw()
# circuit_ir1.print()

# remove special operations
circuit_ir2 = transpiler.remove_special_operations(circuit_ir1)
circuit_ir2.draw()
# circuit_ir2.print()

# translate operations to pulse operations
circuit_ir3 = transpiler.transpile_to_pulse_operations(circuit_ir2)
circuit_ir3.draw()
# circuit_ir3.print()

pulse_schedule = transpiler.generate_pulse_schedule(circuit_ir3)
# pulse_schedule.print()

# Convert to QiliQASM
qasm = QiliQasmConverter.to_qasm(circuit)
print(qasm)

# Parse from QiliQASM
parsed_circuit = QiliQasmConverter.from_qasm(qasm)
