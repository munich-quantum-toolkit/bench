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


def _get_three_qubit_phase_flip_encoding_circuit() -> QuantumCircuit:
    """Encode |0> as (|+++>) and |1> as (|--->)."""
    out = QuantumCircuit(3)
    out.cx(0, 1)
    out.cx(0, 2)
    out.h(0)
    out.h(1)
    out.h(2)
    return out


def _get_three_qubit_bit_flip_encoding_decoding_circuit() -> QuantumCircuit:
    """Encode |0> as |000> and |1> as |111>."""
    out = QuantumCircuit(3)
    out.cx(0, 1)
    out.cx(0, 2)
    return out


def _get_three_qubit_bit_flip_syndrome_extraction_circuit() -> QuantumCircuit:
    """Error in qubit 0 -> syndrome 01, qubit 1 -> 10, qubit 2 -> 11."""
    out = QuantumCircuit(5)
    out.cx(0, 3)
    out.cx(1, 4)
    out.cx(2, 3)
    out.cx(2, 4)
    return out


def _get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit() -> QuantumCircuit:
    """Error in qubits 0-2 -> syndrome 01, qubits 3-5 -> 10, qubits 6-8 -> 11."""
    logical_qubit, phase_flip_syndrome = QuantumRegister(9), QuantumRegister(2)
    out = QuantumCircuit(logical_qubit, phase_flip_syndrome)
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
    qc: QuantumCircuit, bit_flip_syndrome_measurement: ClassicalRegister
) -> None:
    qc.measure(qc.qubits[9 : 9 + 6], bit_flip_syndrome_measurement)
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
            qc.x(index)


def _apply_nine_qubit_shors_code_phase_flip_correction(
    qc: QuantumCircuit, phase_flip_syndrome_measurement: ClassicalRegister
) -> None:
    qc.measure(qc.qubits[-2:], phase_flip_syndrome_measurement)
    with qc.if_test((phase_flip_syndrome_measurement, 0b01)):
        qc.z(0)
    with qc.if_test((phase_flip_syndrome_measurement, 0b10)):
        qc.z(3)
    with qc.if_test((phase_flip_syndrome_measurement, 0b11)):
        qc.z(6)


def _get_three_qubit_phase_flip_decoding_circuit() -> QuantumCircuit:
    out = QuantumCircuit(3)
    out.h(0)
    out.h(1)
    out.h(2)
    out.cx(0, 1)
    out.cx(0, 2)
    return out


@register_benchmark("shors_nine_qubit_code", description="Shor's 9 Qubit Code")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing Shor's 9 Qubit Code.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit (must be a multiple of 17)

    Returns:
        QuantumCircuit: a quantum circuit implementing Shor's 9 Qubit Code
    """
    if num_qubits % 17:
        msg = "num_qubits must be divisible by 17."
        raise ValueError(msg)
    # TODO implement multiples
    logical_qubit = QuantumRegister(9, "q")
    bit_flip_syndrome = QuantumRegister(6, "bs")
    phase_flip_syndrome = QuantumRegister(2, "ps")
    bit_flip_syndrome_measurement = ClassicalRegister(6, "bsm")
    phase_flip_syndrome_measurement = ClassicalRegister(2, "psm")
    qc = QuantumCircuit(
        logical_qubit,
        bit_flip_syndrome,
        phase_flip_syndrome,
        bit_flip_syndrome_measurement,
        phase_flip_syndrome_measurement,
        name="shors_nine_qubit_code",
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
    _apply_nine_qubit_shors_code_bit_flip_correction(qc, bit_flip_syndrome_measurement)
    qc.barrier()
    _apply_nine_qubit_shors_code_phase_flip_correction(qc, phase_flip_syndrome_measurement)
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
    qc.barrier()
    # Measurement
    qc.measure_all()
    return qc
