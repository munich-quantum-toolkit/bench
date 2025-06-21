# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""W state benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("wstate", description="W-State")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the W state.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a quantum circuit implementing the W state
    """
    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="wstate")

    def f_gate(qc: QuantumCircuit, q: QuantumRegister, i: int, j: int, n: int, k: int) -> None:
        theta = np.arccos(np.sqrt(1 / (n - k + 1)))
        qc.ry(-theta, q[j])
        qc.cz(q[i], q[j])
        qc.ry(theta, q[j])

    qc.x(q[-1])

    for m in range(1, num_qubits):
        f_gate(qc, q, num_qubits - m, num_qubits - m - 1, num_qubits, m)

    for k in reversed(range(1, num_qubits)):
        qc.cx(k - 1, k)

    qc.measure_all()

    return qc
