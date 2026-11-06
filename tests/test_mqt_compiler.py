# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Integration tests for MQT Core compilation."""

from __future__ import annotations

import io
import json
from importlib import import_module
from typing import TYPE_CHECKING
from unittest.mock import Mock

import numpy as np
import pytest
from mqt.core import mlir as core
from qiskit import QuantumCircuit, qasm2, qasm3, qpy
from qiskit.circuit import (
    ForLoopOp,
    Gate,
    IfElseOp,
    Measure,
    Parameter,
    ParameterVector,
    Store,
    WhileLoopOp,
)
from qiskit.circuit.library import (
    CXGate,
    GlobalPhaseGate,
    RZGate,
    RZZGate,
    SXGate,
    UGate,
    XGate,
)
from qiskit.quantum_info import Operator, Statevector
from qiskit.transpiler import Target

from mqt.bench import (
    BenchmarkLevel,
    get_benchmark,
    get_benchmark_alg,
    get_benchmark_indep,
    get_benchmark_mapped,
    get_benchmark_native_gates,
)
from mqt.bench.output import OutputFormat, write_circuit
from mqt.bench.targets import get_device, get_target_for_gateset
from mqt.bench.targets.gatesets.ionq import GPI2Gate, GPIGate

if TYPE_CHECKING:
    from mqt.bench.configuration_options import ConfigurationOptions


@pytest.mark.parametrize("name", ["ibm_heron_156", "ibm_nighthawk_120", "ibm_heron_156_fractional"])
def test_ibm_device_compilation(name: str) -> None:
    """Compile the same workload against conventional and fractional IBM devices."""
    target = get_device(name)
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 2)
    circuit.rzz(-0.37, 1, 2)
    result = get_benchmark(circuit, BenchmarkLevel.MAPPED, target=target, compiler="mqt", random_parameters=False)
    assert all(
        target.instruction_supported(
            item.operation.name,
            tuple(result.find_bit(qubit).index for qubit in item.qubits),
            parameters=item.operation.params,
        )
        for item in result.data
    )
    assert result.count_ops().get("rzz", 0) == (2 if name.endswith("fractional") else 0)


def _measurement_probabilities(circuit: QuantumCircuit) -> dict[str, float]:
    """Return terminal measurement probabilities in classical bit order."""
    measured = {
        circuit.find_bit(item.clbits[0]).index: circuit.find_bit(item.qubits[0]).index
        for item in circuit.data
        if item.operation.name == "measure"
    }
    qubits = [measured[bit] for bit in range(circuit.num_clbits)]
    unitary = circuit.copy()
    unitary.remove_final_measurements(inplace=True)
    state = Statevector.from_instruction(unitary)
    return {bits: prob for bits, prob in state.probabilities_dict(qargs=qubits).items() if prob >= 1e-10}


@pytest.mark.parametrize("gateset", ["ibm_heron", "iqm", "quantinuum", "clifford+t+rotations"])
def test_native_equivalence(gateset: str) -> None:
    """Native compilation preserves the unitary, width, name, and user metadata."""
    circuit = QuantumCircuit(3, name="native_test", metadata={"user": {"value": 42}})
    circuit.h(0)
    circuit.ry(0.37, 1)
    circuit.cx(0, 2)
    circuit.cp(0.23, 1, 2)
    circuit.global_phase = 0.17
    original = circuit.copy()
    target = get_target_for_gateset(gateset, 8)
    result = get_benchmark_native_gates(circuit, None, target, compiler="mqt")
    assert circuit == original
    assert result.num_qubits == circuit.num_qubits
    assert result.name == circuit.name
    assert circuit.metadata == {"user": {"value": 42}}
    assert result.metadata["user"] == circuit.metadata["user"]
    assert result.metadata["user"] is not circuit.metadata["user"]
    assert result.metadata["mqt_bench_compiler"]["name"] == "mqt"
    assert Operator(result).equiv(Operator(circuit))
    assert {item.operation.name for item in result.data} <= set(target.operation_names)


def test_symbolic_independent_circuit() -> None:
    """Free parameters survive Core optimization and remain bindable by identity."""
    parameter = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.ry(parameter, 0)
    circuit.cx(0, 1)
    result = get_benchmark_indep(circuit, compiler="mqt", random_parameters=False)
    assert result.parameters == circuit.parameters
    for value in [0.0, 0.7, np.pi]:
        assert Operator(result.assign_parameters({parameter: value})).equiv(
            Operator(circuit.assign_parameters({parameter: value}))
        )


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
@pytest.mark.parametrize("mirror", [False, True])
def test_compiler_options(level: BenchmarkLevel, mirror: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use caller options for compilation and target-specific mirror recompilation."""
    options = core.CompilationOptions(seed=17, mapping=core.MappingOptions(trials=2, iterations=2, lookahead=0))
    adapter = import_module("mqt.bench._mqt_compiler")
    compile_circuit = Mock(wraps=adapter.compile_circuit)
    monkeypatch.setattr(adapter, "compile_circuit", compile_circuit)
    configuration: ConfigurationOptions = {"compiler_options": options, "seed": 42}

    result = get_benchmark(
        "ghz",
        level,
        3,
        target=get_device("iqm_crystal_5"),
        compiler="mqt",
        **configuration,
        generate_mirror_circuit=mirror,
    )
    expected_calls = 2 if mirror and level is not BenchmarkLevel.INDEP else 1
    assert [call.kwargs["options"] for call in compile_circuit.call_args_list] == [options] * expected_calls
    generation = result.metadata["mqt_bench_generation"]
    assert generation["benchmark"] == "ghz"
    assert generation["level"] == level.name.lower()
    assert generation["options"] == {"seed": 42}
    assert generation["mirror"] is mirror
    assert generation["opt_level"] is None
    assert generation["target"] == (None if level is BenchmarkLevel.INDEP else "iqm_crystal_5")
    assert options.seed == 17
    assert options.mapping.trials == 2
    assert options.mapping.iterations == 2
    assert options.mapping.lookahead == 0
    assert result.metadata["mqt_bench_compiler"]["options"] == {
        "seed": 17,
        "enable_statistics": False,
        "enable_timing": False,
        "mapping": {"trials": 2, "iterations": 2, "lookahead": 0, "search_memory_limit": 268435456},
    }


def test_default_mapping_reproducibility() -> None:
    """MQT Bench fixes the seed and trial count instead of depending on CPU count."""
    target = get_device("iqm_crystal_5")
    results = [get_benchmark_mapped("ghz", 3, target, compiler="mqt") for _ in range(2)]
    assert results[0] == results[1]
    defaults = results[0].metadata["mqt_bench_compiler"]["options"]
    assert defaults["seed"] == 10
    assert defaults["mapping"]["trials"] == 8


def test_compiler_options_require_core_compilation() -> None:
    """Reject compiler controls where they would otherwise be silently ignored."""
    options = core.CompilationOptions()
    with pytest.raises(ValueError, match='requires compiler="mqt"'):
        get_benchmark_indep("ghz", 3, compiler_options=options)
    with pytest.raises(ValueError, match="algorithm level does not compile"):
        get_benchmark("ghz", BenchmarkLevel.ALG, 3, compiler="mqt", compiler_options=options)
    with pytest.raises(ValueError, match="algorithm level does not compile"):
        get_benchmark_alg("ghz", 3, compiler_options=options)


def test_mapped_measurement_order() -> None:
    """Routing preserves classical results and respects directed physical gates."""
    target = Target(num_qubits=4)
    for instruction in [XGate(), SXGate(), RZGate(Parameter("theta")), Measure()]:
        target.add_instruction(instruction)
    target.add_instruction(CXGate(), {(1, 0): None, (1, 2): None, (3, 2): None})
    circuit = QuantumCircuit(3, 3)
    circuit.x(0)
    circuit.h(1)
    circuit.cx(0, 2)
    circuit.measure([0, 1, 2], [2, 0, 1])
    result = get_benchmark_mapped(circuit, None, target, compiler="mqt")
    assert result.num_qubits == target.num_qubits
    assert result.layout is None
    assert _measurement_probabilities(result) == pytest.approx(_measurement_probabilities(circuit))
    for item in result.data:
        if item.operation.name == "cx":
            sites = tuple(result.find_bit(qubit).index for qubit in item.qubits)
            assert target.instruction_supported(operation_name="cx", qargs=sites)


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_mirror_without_qiskit_transpilation(level: BenchmarkLevel, monkeypatch: pytest.MonkeyPatch) -> None:
    """A Core mirror keeps both halves and returns only the all-zero outcome."""
    reject_transpile = Mock(side_effect=AssertionError("MQT Core must not call the Qiskit transpiler."))
    target = get_device("iqm_crystal_5") if level == BenchmarkLevel.MAPPED else get_target_for_gateset("ibm_heron", 3)
    monkeypatch.setattr("mqt.bench.benchmark_generation.transpile", reject_transpile)
    monkeypatch.setattr("mqt.bench.benchmark_generation.generate_preset_pass_manager", reject_transpile)
    result = get_benchmark("ghz", level, 3, target=target, compiler="mqt", generate_mirror_circuit=True)
    assert result.name == "ghz_mirror"
    assert result.count_ops().get("barrier", 0) >= 1
    assert result.count_ops().get("cx", 0) + result.count_ops().get("cz", 0) >= 4
    assert _measurement_probabilities(result) == pytest.approx({"0" * result.num_clbits: 1.0})


@pytest.mark.parametrize(
    ("benchmark", "size", "options"),
    [
        ("qft", 3, {}),
        ("grover", 3, {"for_loop": True}),
        ("qwalk", 3, {"for_loop": True}),
        ("dynamic_qft", 3, {}),
        ("ghz_dynamic", 3, {}),
        ("teleportation", 3, {}),
        ("modular_adder", 4, {}),
        ("hrs_cumulative_multiplier", 5, {}),
    ],
)
@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_benchmark_levels(benchmark: str, size: int, options: ConfigurationOptions, level: BenchmarkLevel) -> None:
    """Static and structured Bench circuits pass through every Core compilation level."""
    target = get_device("iqm_crystal_5") if level == BenchmarkLevel.MAPPED else get_target_for_gateset("ibm_heron", 3)
    result = get_benchmark(benchmark, level, size, target=target, compiler="mqt", **options)
    assert result.name == benchmark
    assert result.count_ops().get("measure", 0) > 0
    if benchmark == "dynamic_qft":
        assert result.count_ops().get("if_else", 0) > 0


@pytest.mark.parametrize("gateset", ["ionq_forte", "rigetti", "aqt"])
@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_native_ion_and_fixed_rx_gate_targets(gateset: str, level: BenchmarkLevel) -> None:
    """Core synthesizes provider gates with their native names and parameters."""
    target = get_target_for_gateset(gateset, 2)
    source = QuantumCircuit(2, global_phase=0.19)
    source.u(0.37, 0.21, -0.52, 0)
    source.cx(0, 1)
    source.ry(0.46, 1)
    result = get_benchmark(source, level, target=target, compiler="mqt")
    assert np.allclose(Operator(result).data, Operator(source).data)
    for item in result.data:
        assert target.instruction_supported(
            operation_name=item.operation.name,
            qargs=tuple(result.find_bit(qubit).index for qubit in item.qubits),
            parameters=item.operation.params,
        )
    if gateset.startswith("ionq"):
        assert any(item.operation.name == "gpi2" for item in result.data)
    elif gateset == "rigetti":
        assert any(item.operation.name == "rxpi2" for item in result.data)


@pytest.mark.parametrize("gate_name", ["gpi", "gpi2", "rzz", "rz"])
@pytest.mark.parametrize("symbolic", [False, True])
def test_native_input_gates_preserved(gate_name: str, *, symbolic: bool) -> None:
    """Native gates survive repeated compilation without extra gates."""
    parameter = Parameter("theta") if symbolic else 0.13
    gate = {"gpi": GPIGate, "gpi2": GPI2Gate, "rzz": RZZGate, "rz": RZGate}[gate_name](parameter)
    source = QuantumCircuit(2, global_phase=0.19)
    source.append(gate, range(gate.num_qubits))
    target = get_target_for_gateset("ionq_forte", 2)
    result = source
    for _ in range(2):
        result = get_benchmark_native_gates(result, None, target, compiler="mqt", random_parameters=False)
        assert result.count_ops() == {gate.name: 1}
        assert result.parameters == source.parameters
    for value in [-0.37, 0.0, 0.25]:
        bindings = dict.fromkeys(source.parameters, value)
        assert np.allclose(
            Operator(result.assign_parameters(bindings)).data,
            Operator(source.assign_parameters(bindings)).data,
        )


def test_ion_gates_in_control_flow() -> None:
    """Nested native gates keep radians and conditional measurement results."""
    source = QuantumCircuit(2, 2)
    source.x(0)
    source.measure(0, 0)
    with source.if_test((source.clbits[0], True)):
        source.append(GPIGate(0.13), [1])
    source.measure(1, 1)
    result = get_benchmark_native_gates(source, None, get_target_for_gateset("ionq_forte", 2), compiler="mqt")
    conditional = next(item.operation for item in result.data if isinstance(item.operation, IfElseOp))
    gate = conditional.blocks[0].data[0].operation
    assert gate.name == "gpi"
    assert gate.params == pytest.approx([0.13])
    assert core.QCProgram.from_qiskit(result).to_qco().sample(shots=16, seed=42) == {"11": 16}


def test_compiled_input_layout_is_not_mutated() -> None:
    """Recompile physical wires without mutating the caller's attached layout."""
    source = QuantumCircuit(3, 3)
    source.x(0)
    source.cx(0, 2)
    source.measure([0, 1, 2], [2, 0, 1])
    target = get_target_for_gateset("ibm_heron", 3)
    mapped = core.compile_program(source, target=target, output=core.OutputFormat.QISKIT)
    assert mapped.layout is not None
    original = mapped.copy()
    original_layout = mapped.layout.final_index_layout()
    result = get_benchmark_mapped(mapped, None, target, compiler="mqt")
    assert result.layout is None
    assert _measurement_probabilities(result) == pytest.approx(_measurement_probabilities(source))
    assert mapped == original
    assert mapped.layout is not None
    assert mapped.layout.final_index_layout() == original_layout


@pytest.mark.parametrize("native", [False, True])
def test_incomplete_target_requires_synthesis_basis(*, native: bool) -> None:
    """Even native inputs need a complete basis for target compilation."""
    target = Target(num_qubits=1)
    target.add_instruction(RZGate(np.pi / 4))
    source = QuantumCircuit(1)
    if native:
        source.rz(np.pi / 4, 0)
    else:
        source.h(0)
    with pytest.raises(RuntimeError, match="requires a single-qubit synthesis basis"):
        get_benchmark_native_gates(source, None, target, compiler="mqt")


@pytest.mark.parametrize("mapped", [False, True])
@pytest.mark.parametrize("constraint", ["open_control", "angle_bounds"])
def test_unrepresentable_target_constraints_rejected(constraint: str, *, mapped: bool) -> None:
    """Strict import rejects constraints before compiling even symbolic inputs."""
    theta = Parameter("theta")
    target = Target(num_qubits=2)
    source = QuantumCircuit(2)
    if constraint == "open_control":
        target.add_instruction(UGate(theta, Parameter("phi"), Parameter("lam")))
        target.add_instruction(CXGate(ctrl_state=0), name="cx")
        source.cx(0, 1)
        message = "open controls"
    else:
        target.add_instruction(RZGate(theta), angle_bounds=[(-0.1, 0.1)])
        target.add_instruction(SXGate())
        source.rz(theta, 0)
        message = "parameter constraints"
    compile_circuit = get_benchmark_mapped if mapped else get_benchmark_native_gates
    with pytest.raises(ValueError, match=message):
        compile_circuit(source, None, target, compiler="mqt", random_parameters=False)


@pytest.mark.parametrize("mapped", [False, True])
def test_target_without_applicable_entangler_rejected(*, mapped: bool) -> None:
    """A multi-qubit target needs an applicable entangling capability."""
    target = Target(num_qubits=2)
    target.add_instruction(UGate(*ParameterVector("u", 3)))
    target.add_instruction(CXGate(), {})
    compile_circuit = get_benchmark_mapped if mapped else get_benchmark_native_gates
    error, message = (
        (ValueError, "topology must be connected") if mapped else (RuntimeError, "no usable two-qubit entangler")
    )
    with pytest.raises(error, match=message):
        compile_circuit("ghz", 2, target, compiler="mqt")


@pytest.mark.parametrize("width", [None, 3])
@pytest.mark.parametrize("circuit_width", [1, 2])
def test_native_target_ignores_hardware_topology(width: int | None, circuit_width: int) -> None:
    """Native compilation ignores hardware topology and gates wider than the circuit."""
    target = Target(num_qubits=width)
    target.add_instruction(UGate(*ParameterVector("u", 3)))
    target.add_instruction(CXGate(), {(0, 1): None} if width else None)
    target.add_instruction(Gate("custom_three_qubit", 3, []))
    source = QuantumCircuit(circuit_width, global_phase=0.19)
    source.h(0)
    if circuit_width > 1:
        source.cx(1, 0)
    result = get_benchmark_native_gates(source, None, target, compiler="mqt", random_parameters=False)
    assert result.num_qubits == source.num_qubits
    assert np.allclose(Operator(result).data, Operator(source).data)


@pytest.mark.parametrize("mapped", [False, True])
def test_explicit_global_phase_capability(*, mapped: bool) -> None:
    """Global phase is structural, including under a target alias."""
    target = Target(num_qubits=1)
    target.add_instruction(UGate(*ParameterVector("u", 3)))
    target.add_instruction(GlobalPhaseGate(Parameter("phase")), name="phase_alias")
    source = QuantumCircuit(1, global_phase=0.19)
    source.h(0)
    compile_circuit = get_benchmark_mapped if mapped else get_benchmark_native_gates
    result = compile_circuit(source, None, target, compiler="mqt", random_parameters=False)
    assert np.allclose(Operator(result).data, Operator(source).data)


def test_target_capacity() -> None:
    """Mapped compilation rejects circuits that do not fit on the device."""
    with pytest.raises(ValueError, match="at least as many qubits"):
        get_benchmark_mapped("ghz", 6, get_device("iqm_crystal_5"), compiler="mqt")


def test_compiler_provenance() -> None:
    """Text and binary exports preserve compilation and generation metadata."""
    result = get_benchmark_indep("ghz", 3, compiler="mqt", compiler_options=core.CompilationOptions(seed=17))
    text = io.StringIO()
    write_circuit(result, text, BenchmarkLevel.INDEP)
    assert "// Compiler: mqt " in text.getvalue()
    compiler_options = result.metadata["mqt_bench_compiler"]["options"]
    assert json.loads(text.getvalue().split("// Compiler options: ")[1].splitlines()[0]) == compiler_options
    generation = result.metadata["mqt_bench_generation"]
    assert json.loads(text.getvalue().split("// Generation options: ")[1].splitlines()[0]) == generation
    binary = io.BytesIO()
    write_circuit(result, binary, BenchmarkLevel.INDEP, OutputFormat.QPY)
    binary.seek(0)
    restored = qpy.load(binary)[0]
    assert restored.metadata["mqt_bench_compiler"] == result.metadata["mqt_bench_compiler"]
    assert restored.metadata["mqt_bench_generation"] == generation


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_qiskit_recompilation_provenance(level: BenchmarkLevel) -> None:
    """Recompiling with Qiskit must not retain Core as the last compiler."""
    circuit = get_benchmark_indep("ghz", 3, compiler="mqt")
    target = get_target_for_gateset("ibm_heron", 3)
    result = get_benchmark(circuit, level, target=target)
    assert result.metadata["mqt_bench_compiler"]["name"] == "qiskit"
    assert circuit.metadata["mqt_bench_compiler"]["name"] == "mqt"


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_classical_feed_forward(level: BenchmarkLevel) -> None:
    """Classical destinations and a conditional gate retain their meaning after compilation."""
    circuit = QuantumCircuit(3, 3)
    circuit.x(0)
    circuit.measure(0, 2)
    with circuit.if_test((circuit.clbits[2], True)):
        circuit.x(2)
    circuit.measure([1, 2], [1, 0])
    target = get_device("iqm_crystal_5")
    result = get_benchmark(circuit, level, target=target, compiler="mqt")
    assert core.QCProgram.from_qiskit(result).to_qco().sample(shots=16, seed=42) == {"101": 16}


def test_nested_target_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate block-local operands against their enclosing physical qubit sites."""
    target = Target(num_qubits=3)
    target.add_instruction(XGate(), {(0,): None})
    target.add_instruction(RZGate(Parameter("theta")))
    target.add_instruction(SXGate())
    target.add_instruction(CXGate())
    target.add_instruction(IfElseOp, name="if_else")
    block = QuantumCircuit(1)
    block.x(0)
    circuit = QuantumCircuit(3, 1)
    circuit.if_else((circuit.clbits[0], True), block, QuantumCircuit(1), [2], [])
    monkeypatch.setattr(core, "compile_program", lambda *args, **kwargs: circuit)
    source = QuantumCircuit(3)
    source.x(0)
    get_benchmark_native_gates(source, None, target, compiler="mqt")
    with pytest.raises(ValueError, match=r"instruction 'x'.*qubits \(2,\)"):
        get_benchmark_mapped(source, None, target, compiler="mqt")


def test_mapped_loop_jump() -> None:
    """Allow a loop jump on a target that supports the enclosing control flow."""
    target = Target(num_qubits=2)
    target.add_instruction(UGate(*ParameterVector("u", 3)))
    target.add_instruction(CXGate())
    target.add_instruction(Measure())
    target.add_instruction(ForLoopOp, name="for_loop")
    target.add_instruction(WhileLoopOp, name="while_loop")
    target.add_instruction(IfElseOp, name="if_else")
    target.add_instruction(Store, name="store")

    circuit = QuantumCircuit(2, 2)
    with circuit.for_loop(range(3)):
        circuit.x(0)
        circuit.measure(0, 0)
        with circuit.if_test((circuit.clbits[0], True)):
            circuit.break_loop()
        circuit.x(1)
    circuit.measure(1, 1)

    result = get_benchmark_mapped(circuit, None, target, compiler="mqt")
    assert core.sample(result, shots=4, seed=1) == {"01": 4}


def test_fixed_rx_gate_validation_rejects_unavailable_angle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject exported rotations outside the requested target."""
    target = get_target_for_gateset("rigetti", 2)
    exported = QuantumCircuit(2)
    exported.rx(0.37, 0)
    monkeypatch.setattr(core, "compile_program", lambda *args, **kwargs: exported)
    with pytest.raises(ValueError, match="instruction 'rx' outside the requested target"):
        get_benchmark_native_gates(QuantumCircuit(2), None, target, compiler="mqt")


@pytest.mark.parametrize("ending", ["none", "swap", "barrier", "full_barrier"])
@pytest.mark.parametrize("idle_qubit", [False, True])
def test_native_compilation_preserves_logical_wires(ending: str, *, idle_qubit: bool) -> None:
    """Native circuits and QASM exports preserve logical wires, including idle ones."""
    source = QuantumCircuit(4 if idle_qubit else 3, global_phase=0.37)
    source.x(2)
    source.h(0)
    source.barrier(0, label="inside")
    source.cx(2, 1)
    if ending != "none":
        source.swap(0, 2)
    if ending == "barrier":
        source.barrier(2, label="output")
    elif ending == "full_barrier":
        source.barrier()
    original = source.copy()
    target = get_target_for_gateset("rigetti", source.num_qubits)
    result = get_benchmark_native_gates(source, None, target, compiler="mqt")
    assert source == original
    assert result.layout is None
    assert [
        (item.operation.label, [result.find_bit(qubit).index for qubit in item.qubits])
        for item in result.data
        if item.operation.name == "barrier"
    ] == [
        (item.operation.label, [source.find_bit(qubit).index for qubit in item.qubits])
        for item in source.data
        if item.operation.name == "barrier"
    ]
    np.testing.assert_allclose(Operator(result).data, Operator(source).data, atol=1e-12)
    for fmt in (OutputFormat.QASM2, OutputFormat.QASM3):
        stream = io.StringIO()
        write_circuit(result, stream, BenchmarkLevel.NATIVEGATES, fmt, target)
        restored = (
            qasm2.loads(stream.getvalue(), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
            if fmt is OutputFormat.QASM2
            else qasm3.loads(stream.getvalue())
        )
        assert restored.num_qubits == source.num_qubits
        assert Operator(restored).equiv(Operator(source))


@pytest.mark.parametrize("mapped", [False, True])
@pytest.mark.parametrize("symbolic", [False, True])
def test_fractional_heron_mqt(*, mapped: bool, symbolic: bool) -> None:
    """Core keeps numeric fractional entanglers and safely lowers unknown angles."""
    target = get_target_for_gateset("ibm_heron_fractional", 2)
    compile_circuit = get_benchmark_mapped if mapped else get_benchmark_native_gates
    theta = Parameter("theta")
    angles = (-100.0, -0.37, 0.37, 2.4, 100.0)
    for parameter in (theta,) if symbolic else angles:
        circuit = QuantumCircuit(2)
        circuit.rzz(parameter, 0, 1)
        result = compile_circuit(circuit, None, target, compiler="mqt", random_parameters=False)
        assert all(
            target.instruction_supported(item.operation.name, parameters=item.operation.params) for item in result.data
        )
        assert result.count_ops()["rzz"] == (2 if symbolic else 1)
        for angle in angles if symbolic else (parameter,):
            bound_circuit = circuit.assign_parameters({theta: angle}) if symbolic else circuit
            bound_result = result.assign_parameters({theta: angle}) if symbolic else result
            assert np.allclose(Operator.from_circuit(bound_result).data, Operator(bound_circuit).data)
