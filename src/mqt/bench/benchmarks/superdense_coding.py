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
    r"""Returns a quantum circuit implementing the scalable superdense coding benchmark.

    This benchmark implements the canonical multipartite generalization of
    superdense coding using an :math:`n`-qubit Greenberger-Horne-Zeilinger (GHZ) state
    (Bose, Vedral & Knight 1998, Phys. Rev. A 57, 822; Hao et al. 2001,
    Phys. Rev. A 63, 054301; Hillebrand 2012, arXiv:1210.0650, Section 3.6):

    1. Entanglement preparation:
       A globally entangled :math:`n`-qubit GHZ state
       :math:`\frac{1}{\sqrt{2}}(|0\dots 0\rangle + |1\dots 1\rangle)` is shared
       between a sender (Alice, holding qubits :math:`q_0` to :math:`q_{n-2}`)
       and a receiver (Bob, holding qubit :math:`q_{n-1}`).

    2. Alice's encoding:
       Alice encodes an :math:`n`-bit classical message into the shared state by
       applying local single-qubit Pauli operations (:math:`X, Z`) strictly on
       her :math:`n-1` qubits:

       - Phase flip (:math:`Z`) on qubit :math:`q_0` encodes bit :math:`c_0`.
       - Global bit flip (:math:`X`) on qubit :math:`q_0` encodes bit :math:`c_{n-1}`.
       - Local bit flip (:math:`X`) on qubit :math:`q_i` (:math:`1 \le i \le n-2`)
         when :math:`c_i \oplus c_{n-1} = 1`.
         Because the :math:`X` on qubit :math:`q_0` propagates through the decoding
         CNOT cascade, applying :math:`X` on qubit :math:`q_i` when
         :math:`c_i \oplus c_{n-1} = 1` compensates for this global flip and
         ensures the decoded bit matches :math:`c_i`.

       Alice then transmits her :math:`n-1` physical qubits to Bob, communicating
       :math:`n` classical bits via :math:`n-1` transmitted qubits and pre-shared
       entanglement.

    3. Bob's decoding:
       Bob performs an inverse GHZ-basis transformation (a sequence of CX gates
       followed by a Hadamard gate on qubit :math:`q_0`) and measures in the
       computational basis, deterministically recovering Alice's exact :math:`n`-bit
       classical message.

    For :math:`n = 2`, this protocol reduces identically to the canonical Bennett &
    Wiesner (1992, Phys. Rev. Lett. 69, 2881) 2-qubit superdense coding protocol.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit (must be >= 2).
        message: :math:`n`-bit binary string to encode. If None, defaults to all ones (``'1' * num_qubits``).

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
