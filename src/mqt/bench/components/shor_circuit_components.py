# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Shor's 9-qubit code circuit components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit import AncillaRegister, QuantumCircuit, QuantumRegister

if TYPE_CHECKING:
    from qiskit.circuit import ClassicalRegister


def get_three_qubit_phase_flip_decoding_circuit() -> QuantumCircuit:
    """Create 3-qubit phase-flip decoding circuit.

    Reverses the phase-flip encoding.

    Returns:
        QuantumCircuit: 3-qubit decoding circuit (qubit 0 is the output qubit).
    """
    out = QuantumCircuit(3)
    out.h(0)
    out.h(1)
    out.h(2)
    out.cx(0, 1)
    out.cx(0, 2)
    return out


def get_three_qubit_bit_flip_encoding_decoding_circuit() -> QuantumCircuit:
    """Create 3-qubit bit-flip encoding/decoding circuit.

    Encodes |0> → |000> and |1> → |111>. Self-inverse, so used for both encoding and decoding.

    Returns:
        QuantumCircuit: 3-qubit circuit (qubit 0 is the input/output qubit).
    """
    out = QuantumCircuit(3)
    out.cx(0, 1)
    out.cx(0, 2)
    return out


def get_three_qubit_phase_flip_encoding_circuit() -> QuantumCircuit:
    """Create 3-qubit phase-flip encoding circuit.

    Encodes |0> → |+++> and |1> → |--->

    Returns:
        QuantumCircuit: 3-qubit encoding circuit (qubit 0 is the input qubit).
    """
    out = QuantumCircuit(3)
    out.cx(0, 1)
    out.cx(0, 2)
    out.h(0)
    out.h(1)
    out.h(2)
    return out


def get_three_qubit_bit_flip_syndrome_extraction_circuit() -> QuantumCircuit:
    """Create circuit to extract bit-flip syndrome from a 3-qubit block.

    Uses 2 ancilla qubits to measure parity and identify which qubit (if any) flipped.
    Syndrome mapping: 01 → qubit 0, 10 → qubit 1, 11 → qubit 2, 00 → no error.

    Returns:
        QuantumCircuit: 5-qubit circuit (qubits 0-2 are data, qubits 3-4 are syndrome ancillas).
    """
    out = QuantumCircuit(5)
    out.cx(0, 3)
    out.cx(1, 4)
    out.cx(2, 3)
    out.cx(2, 4)
    return out


def get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit() -> QuantumCircuit:
    """Create circuit to extract phase-flip syndrome across the three 3-qubit blocks.

    Detects which block (if any) experienced a phase flip using 2 ancilla qubits.
    Syndrome mapping: 01 → block 1 (qubits 0-2), 10 → block 2 (qubits 3-5),
    11 → block 3 (qubits 6-8), 00 → no error.

    Returns:
        QuantumCircuit: 11-qubit circuit (qubits 0-8 are data, qubits 9-10 are syndrome ancillas).
    """
    logical_qubit, phase_flip_syndrome = QuantumRegister(9), AncillaRegister(2)
    out = QuantumCircuit(logical_qubit, phase_flip_syndrome)
    # The order on the CNOT gates below is reversed when compared to what one might expect
    #   with the control being the ancilla, and the target being one of the component qubits of the logical qubit
    # This is because we put Hadamards at the starts and ends of the ancilla bits, in order to check the phase
    #   of the logical qubits as opposed to the amplitude.
    # But this also effectively swaps the order of the control and target, so we swap them back to normal
    out.h(phase_flip_syndrome[0])
    out.h(phase_flip_syndrome[1])
    # Syndrome 01 (block 1)
    for i in range(3):
        out.cx(phase_flip_syndrome[0], logical_qubit[i])
    # Syndrome 10 (block 2)
    for i in range(3, 6):
        out.cx(phase_flip_syndrome[1], logical_qubit[i])
    # Syndrome 11 (block 3)
    for i in range(6, 9):
        out.cx(phase_flip_syndrome[0], logical_qubit[i])
        out.cx(phase_flip_syndrome[1], logical_qubit[i])
    out.h(phase_flip_syndrome[0])
    out.h(phase_flip_syndrome[1])
    return out


def apply_nine_qubit_shors_code_bit_flip_correction(
    qc: QuantumCircuit,
    logical_qubit: QuantumRegister,
    bit_flip_syndrome: AncillaRegister,
    bit_flip_syndrome_measurement: ClassicalRegister,
) -> None:
    """Apply bit-flip correction based on syndrome measurement.

    Measures the 6 syndrome qubits and conditionally applies X gates to correct
    bit-flip errors on any of the 9 data qubits.

    Args:
        qc: The quantum circuit to modify.
        logical_qubit: Register containing the 9 data qubits.
        bit_flip_syndrome: Ancilla register containing the 6 syndrome qubits.
        bit_flip_syndrome_measurement: Classical register for syndrome measurement results.
    """
    qc.measure(bit_flip_syndrome, bit_flip_syndrome_measurement)
    # Note that Qiskit uses little-endian bit order
    for index, syndrome in enumerate([
        0b000001,
        0b000010,
        0b000011,
        0b000100,
        0b001000,
        0b001100,
        0b010000,
        0b100000,
        0b110000,
    ]):
        with qc.if_test((bit_flip_syndrome_measurement, syndrome)):
            qc.x(logical_qubit[index])


def apply_nine_qubit_shors_code_phase_flip_correction(
    qc: QuantumCircuit,
    logical_qubit: QuantumRegister,
    phase_flip_syndrome: AncillaRegister,
    phase_flip_syndrome_measurement: ClassicalRegister,
) -> None:
    """Apply phase-flip correction based on syndrome measurement.

    Measures the 2 syndrome qubits and conditionally applies Z gates to correct
    phase-flip errors on the first qubit of the affected block.

    Arguments:
        qc: The quantum circuit to modify.
        logical_qubit: Register containing the 9 data qubits.
        phase_flip_syndrome: Ancilla register containing the 2 syndrome qubits.
        phase_flip_syndrome_measurement: Classical register for syndrome measurement results.
    """
    qc.measure(phase_flip_syndrome, phase_flip_syndrome_measurement)
    with qc.if_test((phase_flip_syndrome_measurement, 0b01)):
        qc.z(logical_qubit[0])
    with qc.if_test((phase_flip_syndrome_measurement, 0b10)):
        qc.z(logical_qubit[3])
    with qc.if_test((phase_flip_syndrome_measurement, 0b11)):
        qc.z(logical_qubit[6])
