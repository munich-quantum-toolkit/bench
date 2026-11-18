# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Multiplier."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit
from qiskit.circuit.library import MultiplierGate

from ._registry import register_benchmark


@register_benchmark("multiplier", description="Multiplier")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Build a multiplier for two equal-width inputs.

    Args:
        num_qubits: Total width, ``4 * n`` for two ``n``-bit operands with ``n >= 1``.

    Returns:
        A circuit that measures only the full product into ``result``, least-significant bit first.

    See Also:
        :class:`qiskit.circuit.library.MultiplierGate`
    """
    if num_qubits % 4 or num_qubits < 4:
        msg = "num_qubits must be an integer ≥ 4 and divisible by 4."
        raise ValueError(msg)

    num_state_qubits = num_qubits // 4
    gate = MultiplierGate(num_state_qubits)

    qc = QuantumCircuit(gate.num_qubits)
    qc.append(gate, qc.qubits)
    result = ClassicalRegister(2 * num_state_qubits, "result")
    qc.add_register(result)
    qc.barrier()
    qc.measure(qc.qubits[2 * num_state_qubits :], result)
    qc.name = "multiplier"

    return qc
