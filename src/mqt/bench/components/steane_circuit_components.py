# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Steane's 7-qubit code circuit components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit import AncillaRegister, QuantumCircuit, QuantumRegister

if TYPE_CHECKING:
    from qiskit.circuit import ClassicalRegister


def get_seven_qubit_steane_code_encoding_circuit() -> QuantumCircuit:
    """Create the 7-qubit Steane code encoding circuit.

    Encodes qubit 0 into the 7-qubit Steane code logical state:
        - |0> -> (|0000000> + |1010101> + |0110011> + |1100110> + |0001111> + |1011010> + |0111100> + |1101001>)
        - |1> -> (|1111111> + |0101010> + |1001100> + |0011001> + |1110000> + |0100101> + |1000011> + |0010110>).

    Returns:
        QuantumCircuit: 7-qubit encoding circuit.
    """
    out = QuantumCircuit(7)
    # H
    out.h(4)
    out.h(5)
    out.h(6)
    # CNOT from 0
    out.cx(0, 1)
    out.cx(0, 2)
    # CNOT from 6
    out.cx(6, 3)
    out.cx(6, 1)
    out.cx(6, 0)
    # CNOT from 5
    out.cx(5, 3)
    out.cx(5, 2)
    out.cx(5, 0)
    # CNOT from 4
    out.cx(4, 3)
    out.cx(4, 2)
    out.cx(4, 1)
    return out


def get_seven_qubit_steane_code_decoding_circuit() -> QuantumCircuit:
    """Create the 7-qubit Steane code decoding circuit.

    Reverses the encoding operation to extract the logical qubit back to qubit 0.

    Returns:
        QuantumCircuit: 7-qubit decoding circuit (qubit 0 is the output qubit).
    """
    return get_seven_qubit_steane_code_encoding_circuit().inverse()


def get_seven_qubit_steane_code_syndrome_extraction_circuit() -> QuantumCircuit:
    """Create the syndrome extraction circuit for the 7-qubit Steane code.

    Extracts bit-flip and phase-flip syndromes using 6 ancilla qubits (3 for each type).

    Bit-flip syndrome extraction:
        Syndrome bits measure the parity of specific qubit subsets corresponding to
        the X-stabilizer generators.

    Phase-flip syndrome extraction:
        Uses Hadamard gates to convert from Z to X basis, and control/target swapped
        CNOTs to extract the phase-flip syndrome

    Syndrome mapping: The 3-bit syndrome value (1-7) directly identifies which
    data qubit experienced an error. Syndrome 0 indicates no error.

    Returns:
        QuantumCircuit: 13-qubit circuit (qubits 0-6 are data, 7-9 are bit-flip
            syndrome ancillas, 10-12 are phase-flip syndrome ancillas).
    """
    logical_qubit, bit_flip_syndrome, phase_flip_syndrome = QuantumRegister(7), AncillaRegister(3), AncillaRegister(3)
    out = QuantumCircuit(logical_qubit, bit_flip_syndrome, phase_flip_syndrome)
    # Bit-flip
    for ctrl in (0, 2, 4, 6):
        out.cx(logical_qubit[ctrl], bit_flip_syndrome[0])
    for ctrl in (1, 2, 5, 6):
        out.cx(logical_qubit[ctrl], bit_flip_syndrome[1])
    for ctrl in (3, 4, 5, 6):
        out.cx(logical_qubit[ctrl], bit_flip_syndrome[2])
    # Phase-flip
    for i in range(3):
        out.h(phase_flip_syndrome[i])
    for targ in (0, 2, 4, 6):
        out.cx(phase_flip_syndrome[0], logical_qubit[targ])
    for targ in (1, 2, 5, 6):
        out.cx(phase_flip_syndrome[1], logical_qubit[targ])
    for targ in (3, 4, 5, 6):
        out.cx(phase_flip_syndrome[2], logical_qubit[targ])
    for i in range(3):
        out.h(phase_flip_syndrome[i])
    return out


def apply_seven_qubit_steane_code_correction(
    qc: QuantumCircuit,
    logical_qubit: QuantumRegister,
    bit_flip_syndrome: AncillaRegister,
    phase_flip_syndrome: AncillaRegister,
    bit_flip_syndrome_measurement: ClassicalRegister,
    phase_flip_syndrome_measurement: ClassicalRegister,
) -> None:
    """Apply error correction based on syndrome measurements.

    Measures the 6 syndrome qubits and conditionally applies X/Z gates to correct
    single-qubit errors on any of the 7 data qubits.

    Args:
        qc: The quantum circuit to modify.
        logical_qubit: Register containing the 7 data qubits.
        bit_flip_syndrome: Register containing the 3 bit-flip syndrome qubits.
        phase_flip_syndrome: Register containing the 3 phase-flip syndrome qubits.
        bit_flip_syndrome_measurement: Classical register for bit-flip syndrome results.
        phase_flip_syndrome_measurement: Classical register for phase-flip syndrome results.
    """
    qc.measure(bit_flip_syndrome, bit_flip_syndrome_measurement)
    qc.measure(phase_flip_syndrome, phase_flip_syndrome_measurement)
    # Bit-flip correction: syndrome value directly indicates which qubit to correct
    for i in range(7):
        with qc.if_test((bit_flip_syndrome_measurement, i + 1)):
            qc.x(logical_qubit[i])
    # Phase-flip correction: syndrome value directly indicates which qubit to correct
    for i in range(7):
        with qc.if_test((phase_flip_syndrome_measurement, i + 1)):
            qc.z(logical_qubit[i])
