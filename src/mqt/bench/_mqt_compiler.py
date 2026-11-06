# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""MQT Core compiler for Qiskit benchmark circuits."""

from __future__ import annotations

from importlib.metadata import version
from typing import TYPE_CHECKING

import mqt.core.mlir as core
from qiskit.circuit import ControlFlowOp

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit
    from qiskit.transpiler import Target


def make_compilation_options(*, seed: int | None = None, mapping_trials: int | None = None) -> core.CompilationOptions:
    """Build the default compiler options with optional CLI overrides."""
    return core.CompilationOptions(
        seed=10 if seed is None else seed,
        mapping=core.MappingOptions(trials=8 if mapping_trials is None else mapping_trials),
    )


def circuit_to_qir(circuit: QuantumCircuit, *, profile: str = "base") -> core.QIRProgram:
    """Lower a circuit to QIR without running target compilation."""
    if profile not in {"base", "adaptive"}:
        msg = f"Unknown QIR profile '{profile}'. Choose 'base' or 'adaptive'."
        raise ValueError(msg)
    if circuit.parameters:
        msg = "QIR export requires bound parameters. Assign all circuit parameters before exporting."
        raise ValueError(msg)
    program = core.QCProgram.from_qiskit(circuit)
    return program.to_qir(core.QIRProfile.BASE if profile == "base" else core.QIRProfile.ADAPTIVE)


def _target_environment(target: Target, num_qubits: int, *, mapped: bool) -> core.TargetEnvironment[QuantumCircuit]:
    """Convert the target, enforcing placement only for mapped compilation."""
    if mapped and (target.num_qubits is None or target.num_qubits < num_qubits):
        msg = "The MQT mapped target must have at least as many qubits as the circuit."
        raise ValueError(msg)
    return core.TargetEnvironment.from_qiskit(target, native_num_qubits=None if mapped else num_qubits, strict=True)


def _validate_target(circuit: QuantumCircuit, target: Target, *, mapped: bool, sites: list[int] | None = None) -> None:
    """Check that exported gates satisfy the target, including inside control flow."""
    sites = list(range(circuit.num_qubits)) if sites is None else sites
    for item in circuit.data:
        operation = item.operation
        if operation.name in {"barrier", "store", "break_loop", "continue_loop"}:
            continue
        qubits = tuple(sites[circuit.find_bit(qubit).index] for qubit in item.qubits)
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


def compile_circuit(
    circuit: QuantumCircuit,
    target: Target | None = None,
    *,
    mapped: bool = False,
    options: core.CompilationOptions | None = None,
) -> QuantumCircuit:
    """Compile through Core and return a Qiskit circuit with compiler provenance.

    Args:
        circuit: Circuit to compile. Core does not modify it.
        target: Optional Qiskit gate set or device target.
        mapped: Whether to enforce physical connectivity and operation placements.
        options: Core compiler controls. Defaults to seed 10 and eight mapping trials.

    Returns:
        A Qiskit circuit. Mapped circuits use physical wires without layout metadata.
    """
    if options is None:
        options = make_compilation_options()
    environment = _target_environment(target, circuit.num_qubits, mapped=mapped) if target is not None else None
    result = core.compile_program(
        circuit, target=environment, options=options, ignore_input_layout=True, include_output_layout=not mapped
    )
    if target is not None:
        _validate_target(result, target, mapped=mapped)
    result.metadata["mqt_bench_compiler"] = {
        "name": "mqt",
        "version": version("mqt-core"),
        "options": {
            "seed": options.seed,
            "enable_statistics": options.enable_statistics,
            "enable_timing": options.enable_timing,
            "mapping": {
                "trials": options.mapping.trials,
                "iterations": options.mapping.iterations,
                "lookahead": options.mapping.lookahead,
                "search_memory_limit": options.mapping.search_memory_limit,
            },
        },
    }
    return result
