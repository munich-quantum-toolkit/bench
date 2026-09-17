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
from typing import TYPE_CHECKING

from qiskit.circuit import ControlFlowOp, Parameter, QuantumCircuit
from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping

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
    from qiskit.transpiler import Target

_CONTROL_FLOW = {
    "if_else": ProgramCapability.FORWARD_BRANCHING,
    "for_loop": ProgramCapability.COUNTED_ITERATION,
    "while_loop": ProgramCapability.CONDITIONAL_LOOP,
    "switch_case": ProgramCapability.MULTIWAY_BRANCHING,
}


def _target_environment(target: Target, num_qubits: int, *, mapped: bool) -> TargetEnvironment:
    """Translate gate support and ordered physical placements to Core."""
    if mapped and (target.num_qubits is None or target.num_qubits < num_qubits):
        msg = "The MQT mapped target must have at least as many qubits as the circuit."
        raise ValueError(msg)
    standard_gates = get_standard_gate_name_mapping()
    operations = [CompilerTarget.OperationCapability("gphase", arity=0, num_parameters=1)]
    for name in target.operation_names:
        if name in {*_CONTROL_FLOW, "break", "continue", "delay", "barrier", "box", "store"}:
            continue
        instruction = target.operation_from_name(name)
        standard = standard_gates.get(name)
        if standard is None or isinstance(instruction, type) or instruction.base_class is not standard.base_class:
            msg = f"The MQT compiler does not support target instruction '{name}'."
            raise ValueError(msg)
        if any(not isinstance(parameter, Parameter) for parameter in instruction.params) or len(
            set(instruction.params)
        ) != len(instruction.params):
            msg = f"The MQT compiler requires unrestricted parameters for target instruction '{name}'."
            raise ValueError(msg)
        placements = target.qargs_for_operation_name(name)
        if placements is not None and not placements:
            continue
        operations.append(
            CompilerTarget.OperationCapability(
                name,
                arity=instruction.num_qubits,
                num_parameters=len(instruction.params),
                site_tuples=sorted(placements) if mapped and placements is not None else None,
            )
        )
    coupling_map = target.build_coupling_map() if mapped else None
    core_target = CompilerTarget(
        target.num_qubits if mapped else num_qubits,
        connectivity=(
            CompilerTarget.Connectivity.all_to_all()
            if coupling_map is None
            else CompilerTarget.Connectivity(list(coupling_map.get_edges()))
        ),
        native_operations=CompilerTarget.NativeOperations(operations),
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


def _check_target(circuit: QuantumCircuit, target: Target, *, mapped: bool, sites: list[int] | None = None) -> None:
    """Check the exported circuit, including the physical sites of nested blocks."""
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
                _check_target(block, target, mapped=mapped, sites=list(qubits))


def circuit_to_qir(circuit: QuantumCircuit, *, profile: str = "base") -> QIRProgram:
    """Lower a circuit to QIR without running target compilation or optimization."""
    if profile not in {"base", "adaptive"}:
        msg = f"Unknown QIR profile '{profile}'. Choose 'base' or 'adaptive'."
        raise ValueError(msg)
    if circuit.parameters:
        msg = "QIR export requires bound parameters. Assign all circuit parameters before exporting."
        raise ValueError(msg)
    program = QCProgram.from_qiskit(circuit)
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
            circuit, qco_pipeline="decompose-multi-controlled,mqt-qco-default", options=options
        ).to_qiskit()
    else:
        environment = _target_environment(target, circuit.num_qubits, mapped=mapped)
        program = QCProgram.from_qiskit(circuit).to_qco()
        program.compile_for_target(environment, options=options)
        result = program.to_qiskit(target=environment.target)
        _check_target(result, target, mapped=mapped)
    result.name = circuit.name
    result.metadata = (circuit.metadata or {}) | {"mqt_bench_compiler": {"name": "mqt", "version": version("mqt-core")}}
    return result
