import pytest

from qilisdk.digital import Circuit

from qililab.digital.circuit_transpiler import CircuitTranspiler
from qililab.digital.circuit_transpiler_passes import (
    AddPhasesToRmwFromRZAndCZPass,
    CancelIdentityPairsPass,
    CanonicalBasisToNativeSetPass,
    CircuitToCanonicalBasisPass,
    CircuitTranspilerPass,
    CustomLayoutPass,
    FuseSingleQubitGatesPass,
    SabreLayoutPass,
    SabreSwapPass,
)
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings


class DummyPass(CircuitTranspilerPass):
    def __init__(self, tag: str, log: list[tuple[str, int]]) -> None:
        self.tag = tag
        self.log = log

    def run(self, circuit: Circuit) -> Circuit:
        self.log.append((self.tag, id(circuit)))
        return circuit


@pytest.fixture
def basic_settings() -> DigitalCompilationSettings:
    return DigitalCompilationSettings(topology=[(0, 1), (1, 2)], gates={})


def test_circuit_transpiler_builds_default_pipeline(basic_settings: DigitalCompilationSettings) -> None:
    transpiler = CircuitTranspiler(basic_settings)

    pipeline_types = [type(p) for p in transpiler._pipeline]
    expected_prefix = [
        CancelIdentityPairsPass,
        CircuitToCanonicalBasisPass,
        FuseSingleQubitGatesPass,
        SabreLayoutPass,
        SabreSwapPass,
        CircuitToCanonicalBasisPass,
        FuseSingleQubitGatesPass,
        CanonicalBasisToNativeSetPass,
        AddPhasesToRmwFromRZAndCZPass,
    ]
    assert pipeline_types == expected_prefix

    for transpiler_pass in transpiler._pipeline:
        assert transpiler_pass.context is transpiler.context

    topology_nodes = sorted(transpiler._topology.node_indices())
    assert topology_nodes == [0, 1, 2]
    assert transpiler._topology.has_edge(0, 1)
    assert transpiler._topology.has_edge(1, 2)


def test_circuit_transpiler_uses_custom_mapping_layout(basic_settings: DigitalCompilationSettings) -> None:
    transpiler = CircuitTranspiler(basic_settings, qubit_mapping={0: 2, 1: 0})

    pipeline_types = [type(p) for p in transpiler._pipeline]
    assert CustomLayoutPass in pipeline_types
    assert SabreLayoutPass not in pipeline_types
    assert SabreSwapPass not in pipeline_types

    custom_layout = next(p for p in transpiler._pipeline if isinstance(p, CustomLayoutPass))
    assert custom_layout.context is transpiler.context


def test_circuit_transpiler_respects_custom_pipeline(basic_settings: DigitalCompilationSettings) -> None:
    log: list[tuple[str, int]] = []
    pipeline = [DummyPass("a", log), DummyPass("b", log)]

    transpiler = CircuitTranspiler(basic_settings, pipeline=pipeline)

    for transpiler_pass in pipeline:
        assert transpiler_pass.context is transpiler.context

    circuit = Circuit(1)
    result = transpiler.run(circuit)

    assert [entry[0] for entry in log] == ["a", "b"]
    first_pass_circuit_id = log[0][1]
    second_pass_circuit_id = log[1][1]
    assert first_pass_circuit_id != id(circuit)
    assert second_pass_circuit_id != first_pass_circuit_id
    assert result is not circuit


        # test with optimizer=True
        rng = np.random.default_rng(seed=42)  # init random number generator

        # circuits are the same
        for _ in range(500):
            nqubits = np.random.randint(4, 10)
            c1 = random_circuit(
                nqubits=nqubits,
                ngates=len(default_gates),
                rng=rng,
                circuit_gates=None,
                exhaustive=True,
            )
            c2_native_gates = transpiler.gates_to_native(c1.queue)
            # check that both c1, c2 are qibo.Circuit
            assert isinstance(c1, Circuit)
            assert isinstance(c2_native_gates, list)
            assert isinstance(c2_native_gates[0], gates.Gate)

            # Build circuit for comparison:
            c2 = Circuit(nqubits)
            [c2.add(gate) for gate in c2_native_gates]

            # check that states have the same absolute coefficients
            z1_exp, z2_exp = compare_exp_z(c1, c2, nqubits)
            assert np.allclose(z1_exp, z2_exp)

    def test_add_phases_from_RZs_and_CZs_to_drags(self, digital_settings):
        """Test that add_phases_from_RZs_and_CZs_to_drags behaves as expected"""
        transpiler = CircuitTranspiler(settings=digital_settings)

        # gate list to optimize
        test_gates = [
            Drag(0, 1, 1),
            gates.CZ(0, 1),
            gates.RZ(1, 1),
            gates.M(0),
            gates.RZ(0, 2),
            Drag(0, 3, 3),
            gates.CZ(0, 2),
            gates.CZ(1, 0),
            Drag(1, 2, 3),
            gates.RZ(1, 0),
        ]
        # resulting gate list from optimization
        result_gates = [
            Drag(0, 1, 1),
            gates.CZ(0, 1),
            gates.M(0),
            Drag(0, 3, 0),
            gates.CZ(0, 2),
            gates.CZ(1, 0),
            Drag(1, 2, -2),
        ]

        # create circuit to test function with
        circuit = Circuit(3)
        circuit.add(test_gates)

        # check that lists are the same
        optimized_gates = transpiler.add_phases_from_RZs_and_CZs_to_drags(circuit.queue, circuit.nqubits)
        for gate_r, gate_opt in zip(result_gates, optimized_gates):
            assert gate_r.name == gate_opt.name
            assert gate_r.parameters == gate_opt.parameters
            assert gate_r.qubits == gate_opt.qubits

    def test_circuit_to_pulses(self, digital_settings):
        """Test translate method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        # test circuit
        circuit = Circuit(5)
        circuit.add(X(0))
        circuit.add(Drag(0, 1, 0.5))
        circuit.add(CZ(3, 2))
        circuit.add(M(0))
        circuit.add(CZ(2, 3))
        circuit.add(CZ(4, 0))
        circuit.add(M(*range(4)))
        circuit.add(Wait(0, t=10))
        circuit.add(Drag(0, 2, 0.5))

        pulse_schedule = transpiler.gates_to_pulses(circuit.queue)

        # test general properties of the pulse schedule
        assert isinstance(pulse_schedule, PulseSchedule)

        # there are 6 different buses + 3 empty for unused flux lines
        assert len(pulse_schedule) == 9

        # we can ignore empty elements from here on
        pulse_schedule.elements = [element for element in pulse_schedule.elements if element.timeline]

        # extract pulse events per bus and separate measurement pulses
        pulse_bus_schedule = {
            pulse_bus_schedule.bus_alias: pulse_bus_schedule.timeline for pulse_bus_schedule in pulse_schedule
        }

        # TODO: I have tested it manually, should add assertions here.


    def test_normalize_angle(self, digital_settings):
        """Test that the angle is normalized properly for drag pulses"""
        c = Circuit(1)
        c.add(Drag(0, 2 * np.pi + 0.1, 0))
        transpiler = CircuitTranspiler(settings=digital_settings)
        pulse_schedule = transpiler.gates_to_pulses(c.queue)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.amplitude, 0.1 * 0.8 / np.pi)
        c = Circuit(1)
        c.add(Drag(0, np.pi + 0.1, 0))
        transpiler = CircuitTranspiler(settings=digital_settings)
        pulse_schedule = transpiler.gates_to_pulses(c.queue)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.amplitude, abs(-0.7745352091052967))

    def test_negative_amplitudes_add_extra_phase(self, digital_settings):
        """Test that transpiling negative amplitudes results in an added PI phase."""
        c = Circuit(1)
        c.add(Drag(0, -np.pi / 2, 0))
        transpiler = CircuitTranspiler(settings=digital_settings)
        pulse_schedule = transpiler.gates_to_pulses(c.queue)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.amplitude, (np.pi / 2) * 0.8 / np.pi)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.phase, 0 + np.pi)

    def test_drag_schedule_error(self, digital_settings):
        """Test error is raised if len(drag schedule) > 1"""
        # append schedule of M(0) to Drag(0) so that Drag(0)'s gate schedule has 2 elements
        digital_settings.gates["Drag(0)"].append(digital_settings.gates["M(0)"][0])
        gate_schedule = digital_settings.gates["Drag(0)"]
        error_string = re.escape(
            f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
        )
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 1))
        transpiler = CircuitTranspiler(settings=digital_settings)
        with pytest.raises(ValueError, match=error_string):
            transpiler.gates_to_pulses(circuit.queue)


    @pytest.mark.parametrize("optimize", [True, False])
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.add_phases_from_RZs_and_CZs_to_drags")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.optimize_gates")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.optimize_transpiled_gates")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.route_circuit")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.gates_to_native")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.gates_to_pulses")
    def test_transpile_circuit(self, mock_to_pulses, mock_to_native, mock_route, mock_opt_trans, mock_opt_circuit, mock_add_phases, optimize, digital_settings):
        """Test transpile_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing=True
        placer = MagicMock()
        router = MagicMock()
        routing_iterations = 7
        transpilation_config = DigitalTranspilationConfig(routing=routing, optimize=optimize, router=router, placer=placer, routing_iterations=routing_iterations)

        # Mock circuit for return values
        mock_circuit = Circuit(5)
        mock_circuit.add(Drag(0, 2*np.pi, np.pi))
        mock_circuit_gates = mock_circuit.queue

        # Mock layout for return values
        mock_layout = [0, 1, 2, 3, 4]

        # Mock schedule for return values
        mock_schedule = PulseSchedule()

        # Mock the return values
        mock_route.return_value = mock_circuit.queue, mock_circuit.nqubits, mock_layout
        mock_opt_circuit.return_value = mock_circuit_gates
        mock_to_native.return_value = mock_circuit_gates
        mock_add_phases.return_value = mock_circuit_gates
        mock_opt_trans.return_value = mock_circuit_gates
        mock_to_pulses.return_value = mock_schedule

        circuit = random_circuit(5, 10, np.random.default_rng())

        schedule, layout = transpiler.transpile_circuit(circuit, transpilation_config)

        # Mandatory asserts in order:
        mock_route.assert_called_once_with(circuit, placer, router, routing_iterations)
        mock_to_native.assert_called_once_with(mock_circuit.queue)
        mock_add_phases.assert_called_once_with(mock_circuit_gates, mock_circuit.nqubits)
        mock_to_pulses.assert_called_once_with(mock_circuit_gates)
        assert (schedule, layout) == (mock_schedule, mock_layout)

        # Asserts if optimize=True:
        if optimize:
            mock_opt_circuit.assert_called_once_with(mock_circuit_gates)
            mock_opt_trans.assert_called_once_with(mock_circuit_gates)
        else:
            mock_opt_circuit.assert_not_called()
            mock_opt_trans.assert_not_called()

            # Test if routing skipped:
            transpilation_config.routing = False
            mock_route.reset_mock()
            _, _ = transpiler.transpile_circuit(circuit, transpilation_config)
            mock_route.assert_not_called()

            # Test if no config is provided:
            mock_route.reset_mock()
            _, _ = transpiler.transpile_circuit(circuit)
            mock_route.assert_not_called()
            mock_opt_circuit.assert_not_called()
            mock_opt_trans.assert_not_called()


    @patch("qililab.digital.circuit_router.CircuitRouter.route")
    def test_route_trivial_circuit(self, mock_route, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 7

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(X(0))
        mock_layout = [0, 1, 2, 3, 4]
        mock_route.return_value = (mock_circuit, mock_layout)

        # Execute the function
        circuit_gates, nqubits, layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)

        # Asserts:
        mock_route.assert_called_once_with(mock_circuit, routing_iterations)
        assert (circuit_gates, nqubits, layout) == (mock_circuit.queue, mock_circuit.nqubits, mock_layout)

    def test_route_circuit_only_needs_remapping_integration(self, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 10

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(gates.CNOT(1, 0))
        mock_circuit.add(gates.CNOT(0, 1))
        mock_circuit.add(gates.CNOT(3, 0))


        # Execute the function
        circuit_gates, nqubits, final_layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)
        output_gates = [(gate.name, gate.qubits) for gate in circuit_gates]

        # Asserts:
        expected_layout = [2, 1, 0, 3, 4]
        expected_gates = [('cx', (1, 2)), ('cx', (2, 1)), ('cx', (3, 2))]

        assert (output_gates, nqubits, final_layout) == (expected_gates, mock_circuit.nqubits, expected_layout)

    def test_route_circuit_swap_needed_integration(self, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 10

        # Mock the return values
        mock_circuit = Circuit(4)
        mock_circuit.add(gates.CNOT(1, 0))
        mock_circuit.add(gates.CNOT(3, 2))


        # Execute the function
        circuit_gates, nqubits, final_layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)
        output_gates = [(gate.name, gate.qubits) for gate in circuit_gates]

        # Asserts:
        expected_gates_and_layout = [
            ([('cx', (2, 0)), ('swap', (2, 3)), ('cx', (2, 1))], [0, 3, 1, 2, 4]),
            ([('cx', (2, 0)), ('swap', (3, 2)), ('cx', (2, 1))], [0, 3, 1, 2, 4]),
            ([('cx', (2, 0)), ('swap', (2, 1)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (2, 0)), ('swap', (1, 2)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (1, 2)), ('swap', (2, 0)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (1, 2)), ('swap', (0, 2)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (1, 2)), ('swap', (2, 3)), ('cx', (2, 0))], [2, 1, 3, 0, 4]),
            ([('cx', (1, 2)), ('swap', (3, 2)), ('cx', (2, 0))], [2, 1, 3, 0, 4]),
            ([('cx', (3, 2)), ('swap', (2, 0)), ('cx', (1, 2))], [2, 1, 0, 3, 4]),
            ([('cx', (3, 2)), ('swap', (0, 2)), ('cx', (1, 2))], [2, 1, 0, 3, 4]),
            ([('cx', (3, 2)), ('swap', (2, 1)), ('cx', (2, 0))], [0, 2, 1, 3, 4]),
            ([('cx', (3, 2)), ('swap', (1, 2)), ('cx', (2, 0))], [0, 2, 1, 3, 4]),

        ]

        assert nqubits == 5 # The routing changes the size to fit that of the topology
        # Test one of the possible routing has been achieved:
        assert (output_gates, final_layout) in expected_gates_and_layout

    def test_route_circuit_complex_integration(self, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 10

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(gates.CNOT(0, 1))
        mock_circuit.add(gates.CNOT(1, 2))
        mock_circuit.add(gates.CNOT(3, 0))
        mock_circuit.add(gates.CNOT(1, 4))
        mock_circuit.add(gates.CNOT(3, 4))
        mock_circuit.add(gates.CNOT(1, 0))


        # Execute the function
        circuit_gates, _, final_layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)
        output_gates = [[gate.name, gate.qubits] for gate in circuit_gates]

        # Undo routing with SWAPS
        for idx, gate in enumerate(output_gates):
            if gate[0] == 'swap':
                output_gates[idx] = None
                mapping_to_do = {gate[1][0]: gate[1][1], gate[1][1]:gate[1][0]}
                for idx_2, gate_2 in enumerate(output_gates[idx+1:]):
                    qubit_1, qubit_2 = gate_2[1]
                    output_gates[idx_2+idx+1][1] = (mapping_to_do.get(qubit_1, qubit_1), mapping_to_do.get(qubit_2, qubit_2))
                # Change layout:
                final_layout[gate[1][0]], final_layout[gate[1][1]] = final_layout[gate[1][1]], final_layout[gate[1][0]]

        # Undo initial mapping
        for idx, gate in enumerate(output_gates):
            if gate is not None:
                output_gates[idx] = gate[0], tuple(final_layout[q] for q in gate[1])

        output_gates = [gate for gate in output_gates if gate is not None]

        # Test you retrieve original circuit:
        assert sorted(output_gates) == sorted([(gate.name, gate.qubits) for gate in mock_circuit.queue])

    @patch("qililab.digital.circuit_transpiler.nx.Graph")
    @patch("qililab.digital.circuit_transpiler.CircuitRouter")
    def test_that_route_circuit_instantiates_Router(self, mock_router, mock_graph, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 7

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(X(0))

        graph_mocking = nx.Graph(transpiler.settings.topology)
        mock_graph.return_value = graph_mocking

        # Execute the function
        with pytest.raises(ValueError, match=re.escape("not enough values to unpack (expected 2, got 0)")):
            transpiler.route_circuit(mock_circuit, iterations=routing_iterations)

        # Asserts:
        mock_router.assert_called_once_with(graph_mocking, None, None)

    def test_DigitalTranspilerConfig(self):
        """Test that the dataclass default values are correct, and that properies give the correct order
        """
        tc = DigitalTranspilationConfig()
        assert tc._attributes_ordered == (False, None, None, 10, False)
