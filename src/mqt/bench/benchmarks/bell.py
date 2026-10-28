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
    r"""Returns a quantum circuit that prepares independent Bell pairs.

    Each pair of neighboring qubits :math:`(2k, 2k + 1)` is prepared in the state
    :math:`\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)` by a Hadamard gate on qubit
    :math:`2k` followed by a CX gate from qubit :math:`2k` to qubit :math:`2k + 1`.
    The pairs do not interact with each other. All qubits are measured at the end.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit. Must be a positive even number.

    Returns:
        QuantumCircuit: A quantum circuit preparing ``num_qubits // 2`` Bell pairs.
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
