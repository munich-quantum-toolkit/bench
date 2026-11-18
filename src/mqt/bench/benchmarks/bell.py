# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Bell-pair benchmark definition."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("bell", description="Bell Pairs")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Prepare independent Bell pairs on neighboring qubits.

    Each pair consists of qubits ``2k`` and ``2k + 1``. A Hadamard followed by a CX
    prepares the pair in an equal superposition of 00 and 11.

    Args:
        num_qubits: Total width. Must be positive and even.

    Returns:
        A circuit that measures both qubits of every pair. Each pair yields 00 or 11 ideally.
    """
    if num_qubits < 2 or num_qubits % 2:
        msg = "num_qubits must be a positive multiple of 2."
        raise ValueError(msg)

    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="bell")
    for k in range(num_qubits // 2):
        qc.h(q[2 * k])
        qc.cx(q[2 * k], q[2 * k + 1])
    qc.measure_all()

    return qc
