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

from ._reference import MetricApplicability, ReferenceSpec, SparseReference
from ._registry import register_benchmark, register_reference


@register_benchmark("ghz", description="GHZ State")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the GHZ state.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
    """
    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="ghz")
    qc.h(q[-1])
    for i in range(1, num_qubits):
        qc.cx(q[num_qubits - i], q[num_qubits - i - 1])
    qc.measure_all()

    return qc


@register_reference("ghz")
def create_reference(num_qubits: int) -> ReferenceSpec:
    """Reference spec for the GHZ circuit.

    The ideal output is an equal superposition of the all-zeros and all-ones
    computational basis states: P(0...0) = P(1...1) = 0.5.

    Arguments:
        num_qubits: number of qubits (same as passed to :func:`create_circuit`).
    """
    entries: dict[str, float] = {"0" * num_qubits: 0.5, "1" * num_qubits: 0.5}
    return ReferenceSpec(
        circuit="ghz",
        n_qubits=num_qubits,
        measured_qubits=list(range(num_qubits)),
        bit_order="qiskit-little-endian",
        reference=SparseReference(entries=entries),
        metrics={
            "hellinger_fidelity": MetricApplicability(applicable=True),
            "tvd": MetricApplicability(applicable=True),
            "linear_xeb": MetricApplicability(applicable=False),
        },
    )
