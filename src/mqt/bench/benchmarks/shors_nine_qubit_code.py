# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Shor's 9 Qubit Code benchmark definition."""

from __future__ import annotations

from qiskit import ClassicalRegister
from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


def _get_three_qubit_bit_flip_encoding_decoding_circuit() -> QuantumCircuit:
    """Create 3-qubit bit-flip encoding/decoding circuit.

    Encodes |0> → |000> and |1> → |111>. Self-inverse, so used for both encoding and decoding.

    Returns:
        QuantumCircuit: 3-qubit circuit (qubit 0 is the input/output qubit).
    """
    out = QuantumCircuit(3)
    out.cx(0, 1)
    out.cx(0, 2)
    return out


def _get_three_qubit_phase_flip_encoding_circuit() -> QuantumCircuit:
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


def _get_three_qubit_phase_flip_decoding_circuit() -> QuantumCircuit:
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


def _get_three_qubit_bit_flip_syndrome_extraction_circuit() -> QuantumCircuit:
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


def _get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit() -> QuantumCircuit:
    """Create circuit to extract phase-flip syndrome across the three 3-qubit blocks.

    Detects which block (if any) experienced a phase flip using 2 ancilla qubits.
    Syndrome mapping: 01 → block 1 (qubits 0-2), 10 → block 2 (qubits 3-5),
    11 → block 3 (qubits 6-8), 00 → no error.

    Returns:
        QuantumCircuit: 11-qubit circuit (qubits 0-8 are data, qubits 9-10 are syndrome ancillas).
    """
    logical_qubit, phase_flip_syndrome = QuantumRegister(9), QuantumRegister(2)
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


def _apply_nine_qubit_shors_code_bit_flip_correction(
    qc: QuantumCircuit,
    logical_qubit: QuantumRegister,
    bit_flip_syndrome: QuantumRegister,
    bit_flip_syndrome_measurement: ClassicalRegister,
) -> None:
    """Apply bit-flip correction based on syndrome measurement.

    Measures the 6 syndrome qubits and conditionally applies X gates to correct
    bit-flip errors on any of the 9 data qubits.

    Arguments:
        qc: The quantum circuit to modify.
        logical_qubit: Register containing the 9 data qubits.
        bit_flip_syndrome: Register containing the 6 syndrome qubits.
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


def _apply_nine_qubit_shors_code_phase_flip_correction(
    qc: QuantumCircuit,
    logical_qubit: QuantumRegister,
    phase_flip_syndrome: QuantumRegister,
    phase_flip_syndrome_measurement: ClassicalRegister,
) -> None:
    """Apply phase-flip correction based on syndrome measurement.

    Measures the 2 syndrome qubits and conditionally applies Z gates to correct
    phase-flip errors on the first qubit of the affected block.

    Arguments:
        qc: The quantum circuit to modify.
        logical_qubit: Register containing the 9 data qubits.
        phase_flip_syndrome: Register containing the 2 syndrome qubits.
        phase_flip_syndrome_measurement: Classical register for syndrome measurement results.
    """
    qc.measure(phase_flip_syndrome, phase_flip_syndrome_measurement)
    with qc.if_test((phase_flip_syndrome_measurement, 0b01)):
        qc.z(logical_qubit[0])
    with qc.if_test((phase_flip_syndrome_measurement, 0b10)):
        qc.z(logical_qubit[3])
    with qc.if_test((phase_flip_syndrome_measurement, 0b11)):
        qc.z(logical_qubit[6])


def _create_single_logical_qubit_circuit(index: int) -> QuantumCircuit:
    """Create a complete Shor code circuit for one logical qubit.

    Builds a circuit with encoding, syndrome extraction, error correction, and decoding stages.

    Arguments:
        index: Index for unique register names (e.g., q0, bs0, ps0 for index=0).

    Returns:
        QuantumCircuit: Circuit with 17 qubits (9 data + 6 bit-flip + 2 phase-flip syndrome)
            and 8 classical bits for syndrome measurements.
    """
    logical_qubit = QuantumRegister(9, f"q{index}")
    bit_flip_syndrome = QuantumRegister(6, f"bs{index}")
    phase_flip_syndrome = QuantumRegister(2, f"ps{index}")
    bit_flip_syndrome_measurement = ClassicalRegister(6, f"bsm{index}")
    phase_flip_syndrome_measurement = ClassicalRegister(2, f"psm{index}")
    qc = QuantumCircuit(
        logical_qubit,
        bit_flip_syndrome,
        phase_flip_syndrome,
        bit_flip_syndrome_measurement,
        phase_flip_syndrome_measurement,
    )
    # == Encoding ==
    # Apply phase flip encoding on the first qubit of each bit-flip block
    qc.compose(
        _get_three_qubit_phase_flip_encoding_circuit(),
        qubits=[logical_qubit[0], logical_qubit[3], logical_qubit[6]],
        inplace=True,
    )
    # Apply bit flip encoding on each block
    qc.compose(_get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[:3], inplace=True)
    qc.compose(_get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[3:6], inplace=True)
    qc.compose(_get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[6:9], inplace=True)
    qc.barrier()
    # == Syndrome extraction ==
    qc.compose(
        _get_three_qubit_bit_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[:3] + bit_flip_syndrome[:2],
        inplace=True,
    )
    qc.compose(
        _get_three_qubit_bit_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[3:6] + bit_flip_syndrome[2:4],
        inplace=True,
    )
    qc.compose(
        _get_three_qubit_bit_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[6:9] + bit_flip_syndrome[4:6],
        inplace=True,
    )
    qc.barrier()
    qc.compose(
        _get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[:] + phase_flip_syndrome[:],
        inplace=True,
    )
    qc.barrier()
    # == Error correction ==
    _apply_nine_qubit_shors_code_bit_flip_correction(
        qc, logical_qubit, bit_flip_syndrome, bit_flip_syndrome_measurement
    )
    qc.barrier()
    _apply_nine_qubit_shors_code_phase_flip_correction(
        qc, logical_qubit, phase_flip_syndrome, phase_flip_syndrome_measurement
    )
    qc.barrier()
    # == Decoding ==
    qc.compose(_get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[:3], inplace=True)
    qc.compose(_get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[3:6], inplace=True)
    qc.compose(_get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[6:9], inplace=True)
    qc.compose(
        _get_three_qubit_phase_flip_decoding_circuit(),
        qubits=[logical_qubit[0], logical_qubit[3], logical_qubit[6]],
        inplace=True,
    )
    return qc


@register_benchmark("shors_nine_qubit_code", description="Shor's 9 Qubit Code")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing Shor's 9 Qubit Code.

    Shor's code is a quantum error-correcting code, capable of correcting arbitrary
    single-qubit errors. It encodes 1 logical qubit into 9 physical qubits using a
    concatenation of the 3-qubit bit-flip and phase-flip repetition codes.

    Encoding:
        1. Phase-flip encoding: The logical qubit is encoded across three blocks using
           |0> → |+++> and |1> → |---> on qubits 0, 3, and 6.
        2. Bit-flip encoding: Each of the three qubits is then encoded using the
           3-qubit repetition code (|0> → |000>, |1> → |111>), giving three blocks
           of three qubits each (0-2, 3-5, 6-8).
        3. So the overall encoding is
           - |0> -> (|000> + |111>) ⊗ (|000> + |111>) ⊗ (|000> + |111>)
           - |1> -> (|000> - |111>) ⊗ (|000> - |111>) ⊗ (|000> - |111>)

    Syndrome Extraction:
        - Bit-flip syndrome: For each block, 2 ancilla qubits measure the parity of
          qubit pairs to detect which qubit (if any) experienced a bit flip.
          Syndrome 01 → qubit 0, syndrome 10 → qubit 1, syndrome 11 → qubit 2.
        - Phase-flip syndrome: 2 ancilla qubits detect phase differences between
          the three blocks. Syndrome 01 → block 1 (qubits 0-2), syndrome 10 → block 2
          (qubits 3-5), syndrome 11 → block 3 (qubits 6-8).

    Error Correction:
        - Bit-flip correction: Based on the 6-bit syndrome measurement, X gates are
          conditionally applied to correct bit flips on any of the 9 data qubits.
        - Phase-flip correction: Based on the 2-bit syndrome measurement, Z gates are
          conditionally applied to the first qubit of the affected block.

    Circuit Structure (per logical qubit):
        - 17 qubits:
            - 9 data qubits (q): The encoded logical qubit
            - 6 bit-flip syndrome qubits (bs): 2 per block for bit-flip detection
            - 2 phase-flip syndrome qubits (ps): For phase-flip detection between blocks
        - 8 classical bits (per logical qubit):
            - 6 bit-flip syndrome measurement bits (bsm)
            - 2 phase-flip syndrome measurement bits (psm)
        - Plus additional measurement bits from the final measure_all

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit (must be divisible by 17)

    Returns:
        QuantumCircuit: a quantum circuit implementing Shor's 9 Qubit Code
    """
    if num_qubits % 17:
        msg = "num_qubits must be divisible by 17."
        raise ValueError(msg)
    if num_qubits < 17:
        msg = "num_qubits must be at least 17."
        raise ValueError(msg)

    num_logical_qubits = num_qubits // 17

    # Start with the first logical qubit circuit as the base
    qc = _create_single_logical_qubit_circuit(0)
    qc.name = "shors_nine_qubit_code"

    # Compose additional logical qubit circuits
    for i in range(1, num_logical_qubits):
        single = _create_single_logical_qubit_circuit(i)
        qc.add_register(*single.qregs)
        qc.add_register(*single.cregs)
        qc.compose(single, qubits=single.qubits, clbits=single.clbits, inplace=True)

    qc.barrier()
    qc.measure_all()
    return qc
