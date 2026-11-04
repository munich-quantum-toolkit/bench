# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VQE realamp ansatz benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit.library import real_amplitudes

from ._registry import register_benchmark

if TYPE_CHECKING:  # pragma: no cover
    from qiskit.circuit import QuantumCircuit


@register_benchmark("vqe_real_amp", description="Real Amplitudes ansatz")
def create_circuit(num_qubits: int, entanglement: str = "reverse_linear", reps: int = 3) -> QuantumCircuit:
    """Returns a quantum circuit implementing the RealAmplitudes ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        entanglement: Qiskit entanglement pattern. Options include ``full``, ``linear``,
            ``reverse_linear``, ``pairwise``, ``circular``, and ``sca``.
        reps: number of repetitions (layers) in the ansatz

    Returns:
        QuantumCircuit: a quantum circuit implementing the RealAmplitudes ansatz
    """
    qc = real_amplitudes(num_qubits, entanglement=entanglement, reps=reps)
    qc.name = "vqe_real_amp"

    qc.measure_all()
    return qc
