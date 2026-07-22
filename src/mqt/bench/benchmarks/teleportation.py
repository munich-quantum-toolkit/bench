# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Teleportation benchmark definition."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


def _teleport_single_block(index: int, state_preparation: QuantumCircuit | None = None) -> QuantumCircuit:
    """Create a teleportation circuit for one block of 3 qubits.

    Each block implements the standard quantum teleportation protocol:
    the state of the source qubit (q0) is teleported to the destination
    qubit (q2) using the Bell pair shared between q1 and q2.

    Arguments:
        index: Index for unique register names (e.g., q0, c0 for index=0).
        state_preparation: Optional 1-qubit circuit applied to the source qubit
            to prepare the state to be teleported. If None, |0⟩ is teleported.

    Returns:
        QuantumCircuit: 3-qubit circuit implementing one teleportation.
    """
    q = QuantumRegister(3, f"q{index}")
    c = ClassicalRegister(2, f"c{index}")
    qc = QuantumCircuit(q, c, name="teleportation")

    qc.h(q[1])
    qc.cx(q[1], q[2])

    if state_preparation is not None:
        qc.append(state_preparation, [q[0]])

    qc.cx(q[0], q[1])
    qc.h(q[0])
    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])

    # Classically-controlled corrections on Bob (q[2])
    with qc.if_test((c[1], 1)):
        qc.x(q[2])
    with qc.if_test((c[0], 1)):
        qc.z(q[2])

    return qc


@register_benchmark("teleportation", description="Quantum Teleportation")
def create_circuit(num_qubits: int, state_preparation: QuantumCircuit | None = None) -> QuantumCircuit:
    """Returns a quantum circuit implementing the quantum teleportation protocol.

    Each group of 3 qubits forms one independent teleportation:
        - qubits ``3k`` are the source qubits (states to be teleported)
        - qubits ``3k + 1`` are Alice's halves of Bell pairs
        - qubits ``3k + 2`` are Bob's halves of Bell pairs (destinations)

    This allows scaling the benchmark to teleport multi-qubit states.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit. Must be divisible by 3.
        state_preparation: Optional 1-qubit circuit applied to each source qubit
            to prepare the state to be teleported. If None, |0⟩ is teleported.

    Returns:
        QuantumCircuit: A quantum circuit implementing the quantum teleportation protocol.
    """
    if num_qubits % 3:
        msg = "num_qubits must be divisible by 3."
        raise ValueError(msg)

    num_blocks = num_qubits // 3

    # Start with the first block as the base
    qc = _teleport_single_block(0, state_preparation)
    qc.name = "teleportation"

    # Compose additional blocks
    for i in range(1, num_blocks):
        single = _teleport_single_block(i, state_preparation)
        qc.add_register(*single.qregs)
        qc.add_register(*single.cregs)
        qc.compose(single, qubits=single.qubits, clbits=single.clbits, inplace=True)

    return qc
