# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
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
    """Returns a quantum circuit implementing the EfficientSU2 ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        entanglement: type of entanglement to use (default: "reverse_linear", other options: "full", "linear", "full", "pairwise", "circular", "sca")
        reps: number of repetitions (layers) in the ansatz

    Returns:
        QuantumCircuit: a quantum circuit implementing the EfficientSU2 ansatz
    """
    qc = efficient_su2(num_qubits, entanglement=entanglement, reps=reps)

    qc.measure_all()
    qc.name = "vqe_su2"

    return qc
