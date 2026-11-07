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
    """Encode a classical message by superdense coding with a shared GHZ state.

    Alice encodes the message on her first ``num_qubits - 1`` qubits and sends them
    to Bob. Bob applies the inverse GHZ preparation and measures all qubits. For
    two qubits this is the Bennett-Wiesner protocol. For the multipartite
    construction see Bose, Vedral & Knight (1998), Phys. Rev. A 57, 822,
    Hao et al. (2001), Phys. Rev. A 63, 054301, and Hillebrand (2012),
    https://arxiv.org/abs/1210.0650, Sec. 3.6.

    Args:
        num_qubits: Total width of the shared GHZ state. Must be at least 2.
        message: Binary string of length ``num_qubits``. Defaults to all ones.

    Returns:
        A circuit that recovers the message in the ideal measurement of ``c``.
        The rightmost character maps to classical bit zero.
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
