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


def _superdense_coding_single_block(index: int, message: str = "11") -> QuantumCircuit:
    """Create a superdense coding circuit for one block of 2 qubits.

    Each block implements the canonical superdense coding protocol:
    1. Alice and Bob share an entangled Bell pair: (|00> + |11>) / sqrt(2).
    2. Alice encodes two classical bits onto her single qubit using local Pauli operations:
       - '00': I
       - '01': Z
       - '10': X
       - '11': X followed by Z (or XZ)
    3. Alice transmits her qubit to Bob.
    4. Bob performs a Bell-basis measurement (CX followed by H) to decode
       and measure both classical bits.

    Arguments:
        index: Index for unique register names (e.g., q0, c0 for index=0).
        message: 2-bit classical string to encode (default: "11").

    Returns:
        QuantumCircuit: 2-qubit circuit implementing one superdense coding instance.
    """
    if len(message) != 2 or not set(message).issubset({"0", "1"}):
        msg = f"Invalid message '{message}'. Must be a 2-bit binary string."
        raise ValueError(msg)

    q = QuantumRegister(2, f"q{index}")
    c = ClassicalRegister(2, f"c{index}")
    qc = QuantumCircuit(q, c, name="superdense_coding")

    # Step 1: Entanglement preparation (Bell state |Phi+>)
    qc.h(q[0])
    qc.cx(q[0], q[1])

    # Step 2: Alice's encoding on qubit 0
    # message[0] encodes the X bit (bit flip), message[1] encodes the Z bit (phase flip)
    if message[0] == "1":
        qc.x(q[0])
    if message[1] == "1":
        qc.z(q[0])

    # Step 3: Bob's Bell-basis decoding and measurement
    qc.cx(q[0], q[1])
    qc.h(q[0])

    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])

    return qc


@register_benchmark("superdense_coding", description="Superdense Coding")
def create_circuit(num_qubits: int, message: str = "11") -> QuantumCircuit:
    """Returns a quantum circuit implementing the superdense coding benchmark.

    Each group of 2 qubits forms one independent superdense coding instance:
        - qubit 2k: Alice's qubit (encoded and transmitted)
        - qubit 2k + 1: Bob's entangled qubit (receiver)

    This allows scaling the benchmark to transmit 2k classical bits using k transmitted qubits.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit. Must be divisible by 2.
        message: 2-bit classical string to encode in each block (default: "11").

    Returns:
        QuantumCircuit: A quantum circuit implementing the superdense coding protocol.
    """
    if num_qubits % 2 != 0:
        msg = "num_qubits must be divisible by 2."
        raise ValueError(msg)

    num_blocks = num_qubits // 2

    # Start with the first block as the base
    qc = _superdense_coding_single_block(0, message)
    qc.name = "superdense_coding"

    # Compose additional blocks
    for i in range(1, num_blocks):
        single = _superdense_coding_single_block(i, message)
        qc.add_register(*single.qregs)
        qc.add_register(*single.cregs)
        qc.compose(single, qubits=single.qubits, clbits=single.clbits, inplace=True)

    return qc
