.. _transpilation:

Transpilation
=============

The transpilation is done automatically, for :meth:`ql.execute()` and :meth:`platform.execute()` methods.
But it can also be done manually, with more control, directly using the :class:`.CircuitTranspiler` class.

The process involves the following steps (by default only: **3.**, **4**., and **6.** run):


1. **Routing and Placement:** Routes and places the circuit's logical qubits onto the chip's physical qubits. The final qubit layout is returned and logged. This step uses the ``placer``, ``router``, and ``routing_iterations`` parameters from ``transpilation_config`` if provided; otherwise, default values are applied. Refer to the :meth:`.CircuitTranspiler.route_circuit()` method for more information.

2. **1st Optimization:** Canceling adjacent pairs of Hermitian gates (H, X, Y, Z, CNOT, CZ, and SWAPs). Refer to the :meth:`.CircuitTranspiler.optimize_gates()` method for more information.

3. **Native Gate Translation:** Translates the circuit into the chip's native gate set (CZ, RZ, Drag, Wait, and M (Measurement)). Refer to the :meth:`.CircuitTranspiler.gates_to_native()` method for more information.

4. **Adding phases to our Drag gates:** commuting RZ gates until the end of the circuit to discard them as virtual Z gates, and due to the phase corrections from CZ. Refer to the :meth:`.CircuitTranspiler.add_phases_from_RZs_and_CZs_to_drags()` method for more information.

5. **2nd Optimization:** Optimizing the resulting Drag gates, by combining multiple pulses into a single one. Refer to the :meth:`.CircuitTranspiler.optimize_transpiled_gates()` method for more information.

6. **Pulse Schedule Conversion:** Converts the native gates into a pulse schedule using calibrated settings from the runcard. Refer to the :meth:`.CircuitTranspiler.gates_to_pulses()` method for more information.

.. note::

    Default steps are only: **3.**, **4**., and **6.**, since they are always needed.

    To do Step **1.** set ``routing=True`` in ``transpilation_config`` (default behavior skips it).

    To do Steps **2.** and **5.** set ``optimize=True`` in ``transpilation_config`` (default behavior skips it).

.. note::

    If the circuit has SWAP gates after a Measurement gate, the automatic routing will not work, better to use the :meth:`.CircuitRouter.route()` method manually, and track the mapping of measurement results before execution.

**Examples:**

For example, the most basic use, would be to automatically transpile during an execute, like:

.. code-block:: python

    from qibo import gates, Circuit
    from qibo.transpiler import ReverseTraversal, Sabre
    import qililab as ql

    # Create circuit:
    c = Circuit(5)
    c.add(gates.CNOT(1, 0))

    # Create transpilation config:
    transpilation = {routing: True, optimize: False, router: Sabre, placer: ReverseTraversal}

    # Create transpiler:
    result = ql.execute(c, runcard="<path_to_runcard>", transpilation_config=transpilation)

Or from a ``platform.execute()`` and using `DigitalTranspilationConfig` for argument hintings instead, like:

.. code-block:: python

    from qibo import gates, Circuit
    from qibo.transpiler import ReverseTraversal, Sabre
    from qililab import build_platform
    from qililab.digital import DigitalTranspilationConfig

    # Create circuit:
    c = Circuit(5)
    c.add(gates.CNOT(1, 0))

    # Create platform:
    platform = build_platform(runcard="<path_to_runcard>")
    transpilation = DigitalTranspilationConfig(routing= True, optimize= False, router= Sabre, placer= ReverseTraversal)

    # Create transpiler:
    result = platform.execute(c, num_avg=1000, repetition_duration=200_000, transpilation_config=transpilation)

Now, if we want more manual control instead, we can instantiate the ``CircuitTranspiler`` object like:

.. code-block:: python

    from qibo import gates
    from qibo.models import Circuit
    from qibo.transpiler.placer import ReverseTraversal, Random
    from qibo.transpiler.router import Sabre
    from qililab import build_platform
    from qililab.digital import CircuitTranspiler

    # Create circuit:
    c = Circuit(5)
    c.add(gates.CNOT(1, 0))

    # Create platform:
    platform = build_platform(runcard="<path_to_runcard>")

    # Create transpiler:
    transpiler = CircuitTranspiler(platform.digital_compilation_settings)

And now, transpile manually, like in the following examples:

.. code-block:: python

    # Default Transpilation (with ReverseTraversal, Sabre, platform's connectivity and optimize = True):
    transpiled_circuit, final_layouts = transpiler.transpile_circuit(c)

    # Or another case, not doing optimization for some reason, and with Non-Default placer:
    transpilation_settings = DigitalTranspilationConfig(placer=Random, optimize=False)
    transpiled_circuit, final_layout = transpiler.transpile_circuit(c, transpilation_config=transpilation_settings)

    # Or also specifying the `router` with kwargs:
    transpilation_settings = DigitalTranspilationConfig(router=(Sabre, {"lookahead": 2}))
    transpiled_circuit, final_layouts = transpiler.transpile_circuit(c, transpilation_config=transpilation_settings)

And even we could only do a single step of the transpilation manually, like in the following, where we will only route:

.. code-block:: python

    # Default Transpilation (with ReverseTraversal, Sabre, platform's connectivity and optimize = True):
    transpiled_circuit, qubits, final_layouts = transpiler.route_circuit(c)

    # Or another case with Non-Default placer:
    transpiled_circuit, qubits, final_layout = transpiler.route_circuit(c, placer=Random)

And finally, if you want to Route a Circuit, but not instantiate any Platform, a CircuitRouter can be used directly, like:

.. code-block:: python

    from qililab.digital import CircuitRouter

    # Create circuit:
    c = Circuit(5)
    c.add(gates.CNOT(1, 0))

    # Create a hardcoded Router with a connectivity graph:
    router = CircuitRouter(connectivity=nx.Graph([(0,1), (0,4), (1,2), (2,4),(2,3)]))
    transpiled_circuit, final_layout = router.route(c)
