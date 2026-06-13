# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""7 Qubit Steane Code benchmark definition."""

from __future__ import annotations

from qiskit import ClassicalRegister
from qiskit.circuit import AncillaRegister, QuantumCircuit, QuantumRegister

from mqt.bench.components.steane_circuit_components import (
    apply_seven_qubit_steane_code_correction,
    get_seven_qubit_steane_code_decoding_circuit,
    get_seven_qubit_steane_code_encoding_circuit,
    get_seven_qubit_steane_code_syndrome_extraction_circuit,
)

from ._registry import register_benchmark


def _create_single_logical_qubit_circuit(index: int) -> QuantumCircuit:
    """Create a complete Steane code circuit for one logical qubit.

    Builds a circuit with encoding, syndrome extraction, error correction, and decoding stages.

    Arguments:
        index: Index for unique register names (e.g., q0, bfs0, pfs0 for index=0).

    Returns:
        QuantumCircuit: Circuit with 13 qubits (7 data + 3 bit-flip + 3 phase-flip syndrome)
            and 7 classical bits (6 for syndrome measurements + 1 for logical qubit measurement).
    """
    logical_qubit = QuantumRegister(7, f"q{index}")
    bit_flip_syndrome = AncillaRegister(3, f"bfs{index}")
    phase_flip_syndrome = AncillaRegister(3, f"pfs{index}")
    bit_flip_syndrome_measurement = ClassicalRegister(3, f"bfsm{index}")
    phase_flip_syndrome_measurement = ClassicalRegister(3, f"pfsm{index}")
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
    qc.compose(
        get_seven_qubit_steane_code_encoding_circuit(),
        qubits=logical_qubit[:],
        inplace=True,
    )
    qc.barrier()
    # == Syndrome extraction ==
    qc.compose(
        get_seven_qubit_steane_code_syndrome_extraction_circuit(),
        qubits=logical_qubit[:] + bit_flip_syndrome[:] + phase_flip_syndrome[:],
        inplace=True,
    )
    qc.barrier()
    # == Error correction ==
    apply_seven_qubit_steane_code_correction(
        qc,
        logical_qubit,
        bit_flip_syndrome,
        phase_flip_syndrome,
        bit_flip_syndrome_measurement,
        phase_flip_syndrome_measurement,
    )
    qc.barrier()
    # == Decoding ==
    qc.compose(
        get_seven_qubit_steane_code_decoding_circuit(),
        qubits=logical_qubit[:],
        inplace=True,
    )
    # == Measurement ==
    qc.measure(logical_qubit[0], logical_qubit_measurement)
    return qc


@register_benchmark("seven_qubit_steane_code", description="7 Qubit Steane Code")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the 7 Qubit Steane Code.

    The Steane code is a quantum error-correcting code that encodes 1 logical qubit
    into 7 physical qubits. It is a CSS (Calderbank-Shor-Steane) code based on the
    classical [7,4,3] Hamming code, capable of correcting arbitrary single-qubit errors.

    Encoding:
        The logical states are encoded as superpositions of 8 codewords:
        - |0_L> = (|0000000> + |1010101> + |0110011> + |1100110>
                 + |0001111> + |1011010> + |0111100> + |1101001>) / sqrt(8)
        - |1_L> = (|1111111> + |0101010> + |1001100> + |0011001>
                 + |1110000> + |0100101> + |1000011> + |0010110>) / sqrt(8)

    Syndrome Extraction:
        - Bit-flip syndrome: 3 ancilla qubits measure X-type stabilizers to detect
          which qubit (if any) experienced a bit flip. The syndrome value (1-7)
          directly identifies the affected qubit.
        - Phase-flip syndrome: 3 ancilla qubits measure Z-type stabilizers to detect
          which qubit (if any) experienced a phase flip. The syndrome value (1-7)
          directly identifies the affected qubit.

    Error Correction:
        - Bit-flip correction: Based on the 3-bit syndrome measurement, X gates are
          conditionally applied to correct bit flips on any of the 7 data qubits.
        - Phase-flip correction: Based on the 3-bit syndrome measurement, Z gates are
          conditionally applied to correct phase flips on any of the 7 data qubits.

    Circuit Structure:
        - 13 qubits (per logical qubit):
            - 7 data qubits (q): The encoded logical qubit
            - 3 bit-flip syndrome qubits (bfs): For X-error detection
            - 3 phase-flip syndrome qubits (pfs): For Z-error detection
        - 7 classical bits (per logical qubit):
            - 3 bit-flip syndrome measurement bits (bfsm)
            - 3 phase-flip syndrome measurement bits (pfsm)
            - 1 logical qubit measurement bit (m)

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit (must be divisible by 13)

    Returns:
        QuantumCircuit: a quantum circuit implementing the 7 Qubit Steane Code
    """
    if num_qubits % 13:
        msg = "num_qubits must be divisible by 13."
        raise ValueError(msg)

    num_logical_qubits = num_qubits // 13

    # Start with the first logical qubit circuit as the base
    qc = _create_single_logical_qubit_circuit(0)
    qc.name = "seven_qubit_steane_code"

    # Compose additional logical qubit circuits
    for i in range(1, num_logical_qubits):
        single = _create_single_logical_qubit_circuit(i)
        qc.add_register(*single.qregs)
        qc.add_register(*single.cregs)
        qc.compose(single, qubits=single.qubits, clbits=single.clbits, inplace=True)

    qc.barrier()
    return qc
