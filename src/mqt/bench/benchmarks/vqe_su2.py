# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VQE su2 ansatz benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit.library import efficient_su2

from ._registry import register_benchmark

if TYPE_CHECKING:  # pragma: no cover
    from qiskit.circuit import QuantumCircuit


@register_benchmark("vqe_su2", description="Efficient SU2 ansatz")
def create_circuit(
    num_qubits: int,
    entanglement: str = "reverse_linear",
    reps: int = 3,
) -> QuantumCircuit:
    """Build an efficient SU(2) ansatz.

    Args:
        num_qubits: Number of qubits in the ansatz.
        entanglement: Qiskit entanglement pattern. Options include ``full``, ``linear``,
            ``reverse_linear``, ``pairwise``, ``circular``, and ``sca``.
        reps: Number of repetitions of the ansatz layers.

    Returns:
        A circuit with parameterized single-qubit rotations and final measurements on all qubits.
    """
    qc = efficient_su2(num_qubits, entanglement=entanglement, reps=reps)

    qc.measure_all()
    qc.name = "vqe_su2"

    return qc
