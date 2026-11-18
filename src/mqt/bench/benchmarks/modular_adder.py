# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Modular Adder."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit
from qiskit.circuit.library import ModularAdderGate

from ._registry import register_benchmark


@register_benchmark("modular_adder", description="Modular Adder")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Build a modular adder for two equal-width operands.

    Args:
        num_qubits: Total width of two equal operands. Must be even and at least 2.

    Returns:
        A circuit that measures only the low ``num_qubits // 2`` bits of the sum into
        ``result``, least-significant bit first.

    See Also:
        :class:`qiskit.circuit.library.ModularAdderGate`
    """
    # Same number of quibts for both registers  → total must be even ≥ 2
    if num_qubits % 2 or num_qubits < 2:
        msg = "num_qubits must be an even integer ≥ 2."
        raise ValueError(msg)

    num_state_qubits = num_qubits // 2
    gate = ModularAdderGate(num_state_qubits)

    qc = QuantumCircuit(gate.num_qubits)
    qc.append(gate, qc.qubits)
    result = ClassicalRegister(num_state_qubits, "result")
    qc.add_register(result)
    qc.barrier()
    qc.measure(qc.qubits[num_state_qubits:], result)
    qc.name = "modular_adder"

    return qc
