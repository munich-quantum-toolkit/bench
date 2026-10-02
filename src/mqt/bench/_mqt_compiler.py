# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Optional MQT Core compiler for Qiskit benchmark circuits."""

from __future__ import annotations

from importlib.metadata import version
from math import inf
from typing import TYPE_CHECKING

from qiskit.circuit import ControlFlowOp
from qiskit.circuit.library import GlobalPhaseGate
from qiskit.transpiler import Target

try:
    from mqt.core.mlir import (
        CompilationOptions,
        CompilerTarget,
        MappingOptions,
        PayloadFormat,
        PayloadSpecification,
        ProgramCapability,
        QCProgram,
        QIRProfile,
        QIRProgram,
        TargetEnvironment,
        compile_program,
    )
except ModuleNotFoundError as exc:
    if exc.name not in {"mqt.core", "mqt.core.mlir"}:
        raise
    msg = 'MQT compilation and QIR export require the pinned MQT Core development version. Install it with: pip install "mqt-bench[mqt]"'
    raise ImportError(msg) from exc

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit

_CONTROL_FLOW = {
    "if_else": ProgramCapability.FORWARD_BRANCHING,
    "for_loop": ProgramCapability.COUNTED_ITERATION,
    "while_loop": ProgramCapability.CONDITIONAL_LOOP,
    "switch_case": ProgramCapability.MULTIWAY_BRANCHING,
}


def _physical_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    """Treat an already mapped circuit's wires as the next compilation input."""
    if circuit.layout is None:
        return circuit
    result = circuit.copy()
    # Qiskit exposes no public setter for layout metadata.
    result._layout = None  # ruff:ignore[private-member-access]
    return result


def _target_environment(target: Target, num_qubits: int, *, mapped: bool) -> TargetEnvironment:
    """Import capabilities strictly; native-gate compilation ignores placement."""
    if mapped and (target.num_qubits is None or target.num_qubits < num_qubits):
        msg = "The MQT mapped target must have at least as many qubits as the circuit."
        raise ValueError(msg)
    structural = {*_CONTROL_FLOW, "break", "continue", "delay", "barrier", "box", "store"}
    names = [
        name
        for name in target.operation_names
        if name not in structural
        and target.qargs_for_operation_name(name) != set()
        and not isinstance(target.operation_from_name(name), GlobalPhaseGate)
    ]
    source = target
    if not mapped:
        names = [
            name
            for name in names
            if isinstance(target.operation_from_name(name), type)
            or target.operation_from_name(name).num_qubits <= num_qubits
        ]
        # A single-qubit gate catalogue needs no physical coupling graph.
        width = max(
            (
                target.operation_from_name(name).num_qubits
                for name in names
                if not isinstance(target.operation_from_name(name), type)
            ),
            default=1,
        )
        source = Target(num_qubits=width)
        for name in names:
            operation = target.operation_from_name(name)
            # Qiskit exposes bound predicates, but not the bounds for copying.
            if target.gate_has_angle_bounds(name) and any(
                not target.supported_angle_bound(name, [bound] * len(operation.params)) for bound in (-inf, inf)
            ):
                msg = f"Cannot represent parameter constraints for '{name}'."
                raise ValueError(msg)
            source.add_instruction(operation, name=name)
    core_target = CompilerTarget.from_qiskit(source, operation_names=names)
    if not mapped:
        core_target = CompilerTarget(
            num_qubits,
            connectivity=CompilerTarget.Connectivity.all_to_all(),
            native_operations=CompilerTarget.NativeOperations(core_target.operations),
        )
    return TargetEnvironment(
        core_target,
        PayloadSpecification(
            PayloadFormat("openqasm", "3.0"),
            capabilities=[
                ProgramCapability(capability) for name, capability in _CONTROL_FLOW.items() if name in target
            ],
        ),
    )


def _validate_target(circuit: QuantumCircuit, target: Target, *, mapped: bool, sites: list[int] | None = None) -> None:
    """Check exported instructions against their enclosing physical qubit sites."""
    sites = list(range(circuit.num_qubits)) if sites is None else sites
    for item in circuit.data:
        operation = item.operation
        qubits = tuple(sites[circuit.find_bit(qubit).index] for qubit in item.qubits)
        if operation.name in {"barrier", "store"}:
            continue
        if not target.instruction_supported(
            operation_name=operation.name,
            qargs=qubits if mapped else None,
            parameters=operation.params if not isinstance(operation, ControlFlowOp) else None,
        ):
            msg = f"MQT Core emitted instruction '{operation.name}' outside the requested target on qubits {qubits}."
            raise ValueError(msg)
        if isinstance(operation, ControlFlowOp):
            for block in operation.blocks:
                _validate_target(block, target, mapped=mapped, sites=list(qubits))


def circuit_to_qir(circuit: QuantumCircuit, *, profile: str = "base") -> QIRProgram:
    """Lower a circuit to QIR without running target compilation or optimization."""
    if profile not in {"base", "adaptive"}:
        msg = f"Unknown QIR profile '{profile}'. Choose 'base' or 'adaptive'."
        raise ValueError(msg)
    if circuit.parameters:
        msg = "QIR export requires bound parameters. Assign all circuit parameters before exporting."
        raise ValueError(msg)
    program = QCProgram.from_qiskit(_physical_circuit(circuit))
    return program.to_qir(QIRProfile.BASE if profile == "base" else QIRProfile.ADAPTIVE)


def compile_circuit(
    circuit: QuantumCircuit,
    target: Target | None = None,
    *,
    mapped: bool = False,
    options: CompilationOptions | None = None,
) -> QuantumCircuit:
    """Compile through Core and return a Qiskit circuit with compiler provenance.

    Args:
        circuit: Circuit to compile. Core does not modify it.
        target: Optional Qiskit gate set or device target.
        mapped: Whether to enforce physical connectivity and operation placements.
        options: Core compiler controls. Defaults to seed 10 and four mapping trials.

    Returns:
        A Qiskit circuit. Mapped circuits use physical wires without layout metadata.
    """
    if options is None:
        options = CompilationOptions(seed=10, mapping=MappingOptions(trials=4))
    if target is None:
        result = compile_program(
            _physical_circuit(circuit), qco_pipeline="decompose-multi-controlled,mqt-qco-default", options=options
        ).to_qiskit()
    else:
        environment = _target_environment(target, circuit.num_qubits, mapped=mapped)
        program = QCProgram.from_qiskit(_physical_circuit(circuit)).to_qco()
        program.compile_for_target(environment, options=options)
        result = program.to_qiskit(target=environment.target)
        _validate_target(result, target, mapped=mapped)
    result._layout = None  # ruff:ignore[private-member-access]
    result.name = circuit.name
    result.metadata = (circuit.metadata or {}) | {"mqt_bench_compiler": {"name": "mqt", "version": version("mqt-core")}}
    return result
