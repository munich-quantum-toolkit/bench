# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VQE realamp ansatz benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from qiskit.circuit.library import real_amplitudes
except ImportError:
    from qiskit.circuit.library import RealAmplitudes as real_amplitudes  # noqa: N813


if TYPE_CHECKING:  # pragma: no cover
    from qiskit.circuit import QuantumCircuit


def create_circuit(num_qubits: int, entanglement: str = "full", reps: int = 3) -> QuantumCircuit:
    """Returns a quantum circuit implementing the RealAmplitudes ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        entanglement: type of entanglement to use (default: "full")
        reps: number of repetitions (layers) in the ansatz

    Returns:
        QuantumCircuit: a quantum circuit implementing the RealAmplitudes ansatz
    """
    qc = real_amplitudes(num_qubits, entanglement=entanglement, reps=reps)
    qc.name = "vqe_real_amp"

    qc.measure_all()
    return qc
