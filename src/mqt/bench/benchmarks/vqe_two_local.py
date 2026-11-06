# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
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
    """Build a variational ansatz with configurable rotation and entanglement layers.

    Args:
        num_qubits: Number of qubits in the ansatz. Each gate in an entanglement layer
            must fit the register. The default CX requires at least two qubits.
        rotation_blocks: Gate names or gates to use in the rotation layers.
        entanglement_blocks: Gate names or gates to use in the entanglement layers.
        entanglement: Qiskit entanglement pattern. Options include ``full``, ``linear``,
            ``reverse_linear``, ``pairwise``, ``circular``, and ``sca``.
        reps: Number of repetitions of the ansatz layers.

    Returns:
        A circuit with the requested gate blocks and final measurements on all qubits.
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
