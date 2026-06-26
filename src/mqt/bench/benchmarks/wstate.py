# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""W state benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._reference import MetricApplicability, ReferenceSpec, UniformReference
from ._registry import register_benchmark, register_reference


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


@register_reference("wstate")
def create_reference(num_qubits: int) -> ReferenceSpec:
    """Reference spec for the W-state circuit.

    The ideal output is the uniform distribution over all ``num_qubits``
    computational basis states of Hamming weight 1: P(x) = 1/num_qubits for
    each bitstring with exactly one '1', and 0 elsewhere.

    The distribution is stored compactly as a ``UniformReference`` so that
    P(x) can be evaluated in O(1) per bitstring without enumerating all states.

    Arguments:
        num_qubits: number of qubits (same as passed to :func:`create_circuit`).
    """
    return ReferenceSpec(
        circuit="wstate",
        n_qubits=num_qubits,
        measured_qubits=list(range(num_qubits)),
        bit_order="qiskit-little-endian",
        reference=UniformReference(predicate="hamming_weight == 1", size=num_qubits),
        metrics={
            "hellinger_fidelity": MetricApplicability(applicable=True),
            "tvd": MetricApplicability(applicable=True),
            "success_probability": MetricApplicability(applicable=True, ideal=1.0),
            "linear_xeb": MetricApplicability(applicable=False),
        },
    )
