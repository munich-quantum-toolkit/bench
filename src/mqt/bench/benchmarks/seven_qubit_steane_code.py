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
from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


def _get_seven_qubit_steane_code_encoding_circuit() -> QuantumCircuit:
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


def _get_seven_qubit_steane_code_decoding_circuit() -> QuantumCircuit:
    """Create the 7-qubit Steane code decoding circuit.

    Reverses the encoding operation to extract the logical qubit back to qubit 0.

    Returns:
        QuantumCircuit: 7-qubit decoding circuit (qubit 0 is the output qubit).
    """
    return _get_seven_qubit_steane_code_encoding_circuit().inverse()


def _get_seven_qubit_steane_code_syndrome_extraction_circuit() -> QuantumCircuit:
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
    logical_qubit, bit_flip_syndrome, phase_flip_syndrome = QuantumRegister(7), QuantumRegister(3), QuantumRegister(3)
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


def _apply_seven_qubit_steane_code_correction(
    qc: QuantumCircuit,
    logical_qubit: QuantumRegister,
    bit_flip_syndrome: QuantumRegister,
    phase_flip_syndrome: QuantumRegister,
    bit_flip_syndrome_measurement: ClassicalRegister,
    phase_flip_syndrome_measurement: ClassicalRegister,
) -> None:
    """Apply error correction based on syndrome measurements.

    Measures the 6 syndrome qubits and conditionally applies X/Z gates to correct
    single-qubit errors on any of the 7 data qubits.

    Arguments:
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


def _create_single_logical_qubit_circuit(index: int) -> QuantumCircuit:
    """Create a complete Steane code circuit for one logical qubit.

    Builds a circuit with encoding, syndrome extraction, error correction, and decoding stages.

    Arguments:
        index: Index for unique register names (e.g., q0, bfs0, pfs0 for index=0).

    Returns:
        QuantumCircuit: Circuit with 13 qubits (7 data + 3 bit-flip + 3 phase-flip syndrome)
            and 6 classical bits for syndrome measurements.
    """
    logical_qubit = QuantumRegister(7, f"q{index}")
    bit_flip_syndrome = QuantumRegister(3, f"bfs{index}")
    phase_flip_syndrome = QuantumRegister(3, f"pfs{index}")
    bit_flip_syndrome_measurement = ClassicalRegister(3, f"bfsm{index}")
    phase_flip_syndrome_measurement = ClassicalRegister(3, f"pfsm{index}")
    qc = QuantumCircuit(
        logical_qubit,
        bit_flip_syndrome,
        phase_flip_syndrome,
        bit_flip_syndrome_measurement,
        phase_flip_syndrome_measurement,
    )
    # == Encoding ==
    qc.compose(
        _get_seven_qubit_steane_code_encoding_circuit(),
        qubits=logical_qubit[:],
        inplace=True,
    )
    qc.barrier()
    # == Syndrome extraction ==
    qc.compose(
        _get_seven_qubit_steane_code_syndrome_extraction_circuit(),
        qubits=logical_qubit[:] + bit_flip_syndrome[:] + phase_flip_syndrome[:],
        inplace=True,
    )
    qc.barrier()
    # == Error correction ==
    _apply_seven_qubit_steane_code_correction(
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
        _get_seven_qubit_steane_code_decoding_circuit(),
        qubits=logical_qubit[:],
        inplace=True,
    )
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
        - 6 classical bits (per logical qubit):
            - 3 bit-flip syndrome measurement bits (bfsm)
            - 3 phase-flip syndrome measurement bits (pfsm)
        - Plus additional measurement bits from the final measure_all

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
    qc.measure_all()
    return qc
