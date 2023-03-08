from qililab.circuit import Circuit
from qililab.circuit.operations import R180, Measure, Rxy, Wait, X

circuit = Circuit(3)
circuit.add(0, Rxy(theta=0, phi=90))
circuit.add(0, Rxy(theta=0, phi=45))
circuit.add(1, R180(phi=0))
circuit.add((0, 1), Wait(t=400))
circuit.add(0, X())
circuit.add(2, X())
circuit.add((0, 1, 2), Measure())
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
