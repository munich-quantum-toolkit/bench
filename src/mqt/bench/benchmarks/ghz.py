# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""GHZ benchmark definition."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("ghz", description="GHZ State")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Prepare a Greenberger-Horne-Zeilinger (GHZ) state.

    Args:
        num_qubits: Number of qubits in the state. Must be at least 1.

    Returns:
        A circuit that measures all qubits. Ideally, the result is all zeros or all ones.
    """
    if num_qubits < 1:
        msg = "num_qubits must be at least 1."
        raise ValueError(msg)

    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="ghz")
    qc.h(q[-1])
    for i in range(1, num_qubits):
        qc.cx(q[num_qubits - i], q[num_qubits - i - 1])
    qc.measure_all()

    return qc
