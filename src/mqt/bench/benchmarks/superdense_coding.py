# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Superdense Coding benchmark definition."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("superdense_coding", description="Superdense Coding")
def create_circuit(num_qubits: int, message: str | None = None) -> QuantumCircuit:
    """Returns a quantum circuit implementing the scalable superdense coding benchmark.

    This benchmark implements the canonical multipartite generalization of
    superdense coding using an n-qubit Greenberger-Horne-Zeilinger (GHZ) state
    (Bose, Vedral & Knight 1998, Phys. Rev. A 57, 822; Hao et al. 2001,
    Phys. Rev. A 63, 054301):

    1. Entanglement preparation:
       A globally entangled n-qubit GHZ state (|0...0> + |1...1>) / sqrt(2) is
       shared between a sender (Alice, holding qubits 0 to n-2) and a receiver
       (Bob, holding qubit n-1).
    2. Alice's encoding:
       Alice encodes an n-bit classical message into the shared state by applying
       local single-qubit Pauli operations (X, Z) strictly on her n-1 qubits:
       - Phase flip (Z) on qubit 0 encodes bit 0.
       - Global bit flip (X) on qubit 0 encodes bit n-1.
       - Local bit flip (X) on qubit i (1 <= i <= n-2) encodes bit i.
       Alice then transmits her n-1 physical qubits to Bob, communicating n
       classical bits via n-1 transmitted qubits and pre-shared entanglement.
    3. Bob's decoding:
       Bob performs an inverse GHZ-basis transformation (a sequence of CX gates
       followed by a Hadamard gate on qubit 0) and measures in the computational
       basis, deterministically recovering Alice's exact n-bit classical message.

    For n = 2, this protocol reduces identically to the canonical Bennett &
    Wiesner (1992, Phys. Rev. Lett. 69, 2881) 2-qubit superdense coding protocol.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit (must be >= 2).
        message: n-bit binary string to encode. If None, defaults to all ones ('1' * num_qubits).

    Returns:
        QuantumCircuit: A quantum circuit implementing scalable superdense coding.
    """
    if num_qubits < 2:
        msg = "num_qubits must be at least 2."
        raise ValueError(msg)

    if message is None:
        message = "1" * num_qubits

    if len(message) != num_qubits or not set(message).issubset({"0", "1"}):
        msg = f"Invalid message '{message}'. Must be a binary string of length {num_qubits}."
        raise ValueError(msg)

    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="superdense_coding")

    # Step 1: Entanglement preparation (GHZ state)
    qc.h(q[0])
    for i in range(1, num_qubits):
        qc.cx(q[0], q[i])
    qc.barrier(q)

    # Step 2: Alice's encoding on her n-1 qubits (q[0] .. q[n-2])
    # Bit ordering: message[-(i+1)] corresponds to the measurement outcome of qubit i.
    bits = [int(message[-(i + 1)]) for i in range(num_qubits)]
    if bits[0] == 1:
        qc.z(q[0])
    if bits[num_qubits - 1] == 1:
        qc.x(q[0])
    for i in range(1, num_qubits - 1):
        if (bits[i] ^ bits[num_qubits - 1]) == 1:
            qc.x(q[i])
    qc.barrier(q)

    # Step 3: Bob's decoding (joint GHZ-basis measurement)
    for i in range(num_qubits - 1, 0, -1):
        qc.cx(q[0], q[i])
    qc.h(q[0])

    for i in range(num_qubits):
        qc.measure(q[i], c[i])

    return qc
