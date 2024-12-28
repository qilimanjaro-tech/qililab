Transpilation
=============

The transpilation is done automatically, for :meth:`ql.execute()` and :meth:`platform.execute()` methods.

But it can also be done manually, with more control, directly using the :class:`.CircuitTranspiler` class.

The process involves the following steps:

1. \*)Routing and Placement: Routes and places the circuit's logical qubits onto the chip's physical qubits. The final qubit layout is returned and logged. This step uses the ``placer``, ``router``, and ``routing_iterations`` parameters from ``transpile_config`` if provided; otherwise, default values are applied.

2. \*\*)Canceling adjacent pairs of Hermitian gates (H, X, Y, Z, CNOT, CZ, and SWAPs).

3. Native Gate Translation: Translates the circuit into the chip's native gate set (CZ, RZ, Drag, Wait, and M (Measurement)).

4. Commuting virtual RZ gates and adding phase corrections from CZ.

5. \*\*)Optimizing the resulting Drag gates, by combining multiple pulses into a single one.

6. Pulse Schedule Conversion: Converts the native gates into a pulse schedule using calibrated settings from the runcard.

.. note::

    \*) If ``routing=False`` in ``transpile_config`` (default behavior), step 1. is skipped.

    \*\*) If ``optimize=False`` in ``transpile_config`` (default behavior), steps 2. and 5. are skipped.

    The rest of steps are always done.

**Examples:**

If we instantiate some ``Circuit``, ``Platform`` and ``CircuitTranspiler`` objects like:

.. code-block:: python

    from qibo import gates
    from qibo.models import Circuit
    from qibo.transpiler.placer import ReverseTraversal, Trivial
    from qibo.transpiler.router import Sabre
    from qililab import build_platform
    from qililab.circuit_transpiler import CircuitTranspiler

    # Create circuit:
    c = Circuit(5)
    c.add(gates.CNOT(1, 0))

    # Create platform:
    platform = build_platform(runcard="<path_to_runcard>")

    # Create transpiler:
    transpiler = CircuitTranspiler(platform.digital_compilation_settings)

Now we can transpile like, in the following examples:

.. code-block:: python

    # Default Transpilation (with ReverseTraversal, Sabre, platform's connectivity and optimize = True):
    transpiled_circuit, final_layouts = transpiler.transpile_circuit(c)

    # Or another case, not doing optimization for some reason, and with Non-Default placer:
    transpiled_circuit, final_layout = transpiler.transpile_circuit(c, placer=Trivial, optimize=False)

    # Or also specifying the `router` with kwargs:
    transpiled_circuit, final_layouts = transpiler.transpile_circuit(c, router=(Sabre, {"lookahead": 2}))
