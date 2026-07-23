.. _transpilation:

Transpilation
=============

Transpilation is done automatically when a circuit is compiled or executed through
:meth:`.Platform.compile_circuit` and :meth:`.Platform.execute_circuit`. It can also be run manually, with more
control, directly through the :class:`.CircuitTranspiler` class.

The transpiler runs a linear pipeline of ``CircuitTranspilerPass`` objects. Each pass has a single, narrowly defined
responsibility, and the circuit is passed from one pass to the next. The default pipeline performs, in order:

1. **Cancel identity pairs:** removes adjacent pairs of Hermitian gates that cancel out (``CancelIdentityPairsPass``).

2. **Canonical basis + single-qubit fusion:** rewrites the circuit into a canonical basis and fuses consecutive
   single-qubit gates (``CircuitToCanonicalBasisPass``, ``FuseSingleQubitGatesPass``).

3. **Layout and routing:** maps the circuit's logical qubits onto the chip's physical qubits and inserts the SWAPs
   required by the chip topology. When no explicit ``qubit_mapping`` is given this uses ``SabreLayoutPass`` +
   ``SabreSwapPass``; when a mapping is given it uses ``CustomLayoutPass``.

4. **Native gate translation:** translates the routed circuit into the chip's native gate set
   (``CanonicalBasisToNativeSetPass``).

5. **Drag phase corrections:** commutes RZ gates and applies the phase corrections coming from the CZ gates onto the
   Drag gates (``AddPhasesToRmwFromRZAndCZPass``).

The conversion of the transpiled, native-gate circuit into an executable :class:`.QProgram` is performed separately by
``CircuitToQProgramCompiler`` (invoked by :meth:`.Platform.compile_circuit`).

**Example:**

For most use cases, transpilation happens implicitly when you compile or execute a circuit:

.. code-block:: python

    from qilisdk.digital import Circuit, RY, CZ, M
    from qililab import build_platform

    # Create a circuit:
    circuit = Circuit(2)
    circuit.add(RY(0, theta=0.2))
    circuit.add(CZ(0, 1))
    circuit.add(M(1))

    # Build the platform and execute (transpilation runs automatically):
    platform = build_platform(runcard="<path_to_runcard>")
    result = platform.execute_circuit(circuit, nshots=1000)

If you want manual control over the transpilation, instantiate a :class:`.CircuitTranspiler` with the platform's
digital compilation settings and call :meth:`.CircuitTranspiler.run`:

.. code-block:: python

    from qilisdk.digital import Circuit, RY, CZ, M
    from qililab import build_platform
    from qililab.digital import CircuitTranspiler

    # Create a circuit:
    circuit = Circuit(2)
    circuit.add(RY(0, theta=0.2))
    circuit.add(CZ(0, 1))
    circuit.add(M(1))

    # Build the platform and transpile:
    platform = build_platform(runcard="<path_to_runcard>")
    transpiler = CircuitTranspiler(platform.digital_compilation_settings)

    transpiled_circuit = transpiler.run(circuit)
    final_layout = transpiler.context.final_layout

To use an explicit logical-to-physical qubit mapping instead of the automatic layout/routing passes, pass
``qubit_mapping`` to the constructor:

.. code-block:: python

    transpiler = CircuitTranspiler(platform.digital_compilation_settings, qubit_mapping={0: 2, 1: 3})
    transpiled_circuit = transpiler.run(circuit)

You can also supply a custom ``pipeline`` (a list of ``CircuitTranspilerPass`` objects) to the constructor to fully
control which passes run and in which order.
