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


def _physical_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    """Treat an already mapped circuit's wires as the next compilation input."""
    if circuit.layout is None:
        return circuit
    result = circuit.copy()
    # Qiskit exposes no public setter for layout metadata.
    result._layout = None  # ruff:ignore[private-member-access]
    return result


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
        options = core.CompilationOptions(seed=10, mapping=core.MappingOptions(trials=8))
    environment = _target_environment(target, circuit.num_qubits, mapped=mapped) if target is not None else None
    result = core.compile_program(
        _physical_circuit(circuit), target=environment, output=core.OutputFormat.QISKIT, options=options
    )
    if target is not None:
        if mapped:
            result._layout = None  # ruff:ignore[private-member-access]
        _validate_target(result, target, mapped=mapped)
    result.metadata = result.metadata | {
        "mqt_bench_compiler": {
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
    }
    return result
