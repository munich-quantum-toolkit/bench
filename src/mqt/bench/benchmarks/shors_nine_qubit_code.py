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
from qiskit.circuit import AncillaRegister, QuantumCircuit, QuantumRegister

from mqt.bench.components.shor_circuit_components import (
    apply_nine_qubit_shors_code_bit_flip_correction,
    apply_nine_qubit_shors_code_phase_flip_correction,
    get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit,
    get_three_qubit_bit_flip_encoding_decoding_circuit,
    get_three_qubit_bit_flip_syndrome_extraction_circuit,
    get_three_qubit_phase_flip_decoding_circuit,
    get_three_qubit_phase_flip_encoding_circuit,
)

from ._registry import register_benchmark


def _create_single_logical_qubit_circuit(index: int) -> QuantumCircuit:
    """Create a complete Shor code circuit for one logical qubit.

    Builds a circuit with encoding, syndrome extraction, error correction, and decoding stages.

    Arguments:
        index: Index for unique register names (e.g., q0, bs0, ps0 for index=0).

    Returns:
        QuantumCircuit: Circuit with 17 qubits (9 data + 6 bit-flip + 2 phase-flip syndrome)
            and 9 classical bits (8 for syndrome measurements + 1 for logical qubit measurement).
    """
    logical_qubit = QuantumRegister(9, f"q{index}")
    bit_flip_syndrome = AncillaRegister(6, f"bs{index}")
    phase_flip_syndrome = AncillaRegister(2, f"ps{index}")
    bit_flip_syndrome_measurement = ClassicalRegister(6, f"bsm{index}")
    phase_flip_syndrome_measurement = ClassicalRegister(2, f"psm{index}")
    logical_qubit_measurement = ClassicalRegister(1, f"m{index}")
    qc = QuantumCircuit(
        logical_qubit,
        bit_flip_syndrome,
        phase_flip_syndrome,
        bit_flip_syndrome_measurement,
        phase_flip_syndrome_measurement,
        logical_qubit_measurement,
    )
    # == Encoding ==
    # Apply phase flip encoding on the first qubit of each bit-flip block
    qc.compose(
        get_three_qubit_phase_flip_encoding_circuit(),
        qubits=[logical_qubit[0], logical_qubit[3], logical_qubit[6]],
        inplace=True,
    )
    # Apply bit flip encoding on each block
    qc.compose(get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[:3], inplace=True)
    qc.compose(get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[3:6], inplace=True)
    qc.compose(get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[6:9], inplace=True)
    qc.barrier()
    # == Syndrome extraction ==
    qc.compose(
        get_three_qubit_bit_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[:3] + bit_flip_syndrome[:2],
        inplace=True,
    )
    qc.compose(
        get_three_qubit_bit_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[3:6] + bit_flip_syndrome[2:4],
        inplace=True,
    )
    qc.compose(
        get_three_qubit_bit_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[6:9] + bit_flip_syndrome[4:6],
        inplace=True,
    )
    qc.barrier()
    qc.compose(
        get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit(),
        qubits=logical_qubit[:] + phase_flip_syndrome[:],
        inplace=True,
    )
    qc.barrier()
    # == Error correction ==
    apply_nine_qubit_shors_code_bit_flip_correction(qc, logical_qubit, bit_flip_syndrome, bit_flip_syndrome_measurement)
    qc.barrier()
    apply_nine_qubit_shors_code_phase_flip_correction(
        qc, logical_qubit, phase_flip_syndrome, phase_flip_syndrome_measurement
    )
    qc.barrier()
    # == Decoding ==
    qc.compose(get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[:3], inplace=True)
    qc.compose(get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[3:6], inplace=True)
    qc.compose(get_three_qubit_bit_flip_encoding_decoding_circuit(), qubits=logical_qubit[6:9], inplace=True)
    qc.compose(
        get_three_qubit_phase_flip_decoding_circuit(),
        qubits=[logical_qubit[0], logical_qubit[3], logical_qubit[6]],
        inplace=True,
    )
    # == Measurement ==
    qc.measure(logical_qubit[0], logical_qubit_measurement)
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
        - 9 classical bits:
            - 6 bit-flip syndrome measurement bits (bsm)
            - 2 phase-flip syndrome measurement bits (psm)
            - 1 logical qubit measurement bit (m)

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit (must be divisible by 17)

    Returns:
        QuantumCircuit: a quantum circuit implementing Shor's 9 Qubit Code
    """
    if num_qubits % 17:
        msg = "num_qubits must be divisible by 17."
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
    return qc
