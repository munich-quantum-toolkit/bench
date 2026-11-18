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


@register_benchmark("teleportation", description="Quantum Teleportation")
def create_circuit(num_qubits: int, state_preparation: QuantumCircuit | None = None) -> QuantumCircuit:
    """Teleport a one-qubit state independently in each group of three qubits.

    In group ``k``, qubit ``3k`` is the source and qubits ``3k + 1`` and ``3k + 2``
    share a Bell pair. The first two measurements control the X and Z corrections
    on the destination, qubit ``3k + 2``.

    Args:
        num_qubits: Total width. Must be a positive multiple of 3.
        state_preparation: Optional one-qubit circuit with no classical bits, applied
            to each source. The default source state is the computational zero state.

    Returns:
        A circuit with two intermediate measurement bits per group. It measures each
        destination into the corresponding bit of ``final_measurement``.
    """
    if num_qubits < 3 or num_qubits % 3:
        msg = "num_qubits must be a positive multiple of 3."
        raise ValueError(msg)
    if state_preparation is not None and state_preparation.num_qubits != 1:
        msg = "state_preparation must be a 1-qubit circuit."
        raise ValueError(msg)
    if state_preparation is not None and state_preparation.num_clbits != 0:
        msg = "state_preparation cannot contain classical bits."
        raise ValueError(msg)

    num_blocks = num_qubits // 3

    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="teleportation")

    destinations = []
    for k in range(num_blocks):
        source, alice, bob = q[3 * k], q[3 * k + 1], q[3 * k + 2]
        mid_measure = ClassicalRegister(2, f"mid_measurement{k}")
        qc.add_register(mid_measure)

        # Share a Bell pair between Alice and Bob
        qc.h(alice)
        qc.cx(alice, bob)

        # Prepare the state to be teleported on the source qubit
        if state_preparation is not None:
            qc.append(state_preparation, [source])

        # Bell-basis measurement of the source and Alice's qubit
        qc.cx(source, alice)
        qc.h(source)
        qc.measure(source, mid_measure[0])
        qc.measure(alice, mid_measure[1])

        # Classically controlled corrections on Bob's qubit
        with qc.if_test((mid_measure[1], 1)):
            qc.x(bob)
        with qc.if_test((mid_measure[0], 1)):
            qc.z(bob)

        destinations.append(bob)

    final_measure = ClassicalRegister(num_blocks, "final_measurement")
    qc.add_register(final_measure)
    qc.measure(destinations, final_measure)

    return qc
