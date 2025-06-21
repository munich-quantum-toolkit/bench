# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VQE twolocal ansatz benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit.library.n_local.n_local import n_local

from ._registry import register_benchmark

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

    from qiskit.circuit import Gate, QuantumCircuit


@register_benchmark("vqe_two_local", description="Two-local ansatz")
def create_circuit(
    num_qubits: int,
    rotation_blocks: str | Gate | Iterable[str | Gate] = "ry",
    entanglement_blocks: str | Gate | Iterable[str | Gate] = "cx",
    entanglement: str = "full",
    reps: int = 3,
) -> QuantumCircuit:
    """Returns a quantum circuit implementing the TwoLocal ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        rotation_blocks: type of rotation gates to use (default: "ry", other options can be arbitrary single-qubit gates)
        entanglement_blocks: type of entanglement gates to use (default: "cx", other options can be arbitrary multi-qubit gates)
        entanglement: type of entanglement to use (default: "full", other options: "reverse_linear", "linear", "full", "pairwise", "circular", "sca")
        reps: number of repetitions (layers) in the ansatz

    Returns:
        QuantumCircuit: a quantum circuit implementing the TwoLocal ansatz
    """
    qc = n_local(
        num_qubits,
        rotation_blocks=rotation_blocks,
        entanglement_blocks=entanglement_blocks,
        entanglement=entanglement,
        reps=reps,
    )

    qc.measure_all()
    qc.name = "vqe_two_local"

    return qc
