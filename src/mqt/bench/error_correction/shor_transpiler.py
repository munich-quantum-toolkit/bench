# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Transpiler that encodes circuits with Shor's 9-qubit code."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from qiskit.circuit.library import IGate

from mqt.bench.components.shor_circuit_components import (
    apply_nine_qubit_shors_code_bit_flip_correction,
    apply_nine_qubit_shors_code_phase_flip_correction,
    get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit,
    get_three_qubit_bit_flip_encoding_decoding_circuit,
    get_three_qubit_bit_flip_syndrome_extraction_circuit,
    get_three_qubit_phase_flip_encoding_circuit,
)

from .ec_transpiler import ECTranspiler, LogicalQubit

if TYPE_CHECKING:
    from qiskit import QuantumCircuit, QuantumRegister
    from qiskit.circuit import Gate


class ShorTranspiler(ECTranspiler):
    """Encodes a QuantumCircuit with Shor's 9-qubit code.

    X, Y, Z, and CX have handlers. Shor's 9-qubit code has no transversal H, T, or Tdg, so these
    gates become placeholders.
    """

    # Structure of Shor's 9-qubit code
    SHOR_BLOCK_SIZE = 3
    SHOR_NUM_BLOCKS = 3
    SHOR_PHASE_FLIP_TARGETS: ClassVar[list[int]] = [0, 3, 6]

    CODE_NAME = "shor"
    BLOCK_SIZE = SHOR_BLOCK_SIZE * SHOR_NUM_BLOCKS
    BIT_FLIP_SYNDROME_SIZE = 6
    PHASE_FLIP_SYNDROME_SIZE = 2
    TARGET_GATE_SET: ClassVar[list[str]] = ["id", "h", "x", "y", "z", "cx", "t", "tdg"]
    TRANSVERSAL_GATES: ClassVar[dict[str, Gate]] = {"id": IGate()}

    def _apply_encoding(self, qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply the encoding of Shor's 9-qubit code to a physical data register."""
        # Phase flip encoding on the first qubit of each block
        qc.compose(
            get_three_qubit_phase_flip_encoding_circuit(),
            qubits=[physical_data_register[i] for i in self.SHOR_PHASE_FLIP_TARGETS],
            inplace=True,
        )

        # Bit flip encoding on each block
        for i in range(self.SHOR_NUM_BLOCKS):
            qc.compose(
                get_three_qubit_bit_flip_encoding_decoding_circuit(),
                qubits=physical_data_register[i * self.SHOR_BLOCK_SIZE : (i + 1) * self.SHOR_BLOCK_SIZE],
                inplace=True,
            )

    def _apply_decoding(self, qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply the decoding of Shor's 9-qubit code to a physical data register."""
        for i in range(self.SHOR_NUM_BLOCKS):
            qc.compose(
                get_three_qubit_bit_flip_encoding_decoding_circuit().inverse(),
                qubits=physical_data_register[i * self.SHOR_BLOCK_SIZE : (i + 1) * self.SHOR_BLOCK_SIZE],
                inplace=True,
            )
        qc.compose(
            get_three_qubit_phase_flip_encoding_circuit().inverse(),
            qubits=[physical_data_register[i] for i in self.SHOR_PHASE_FLIP_TARGETS],
            inplace=True,
        )

    def _logical_x(self, logical_qubit_index: int) -> None:
        """Apply logical X as Z on the first qubit of each block (Z_0 Z_3 Z_6).

        Z on one qubit of a block flips the phase of the whole block.
        """
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in (physical_data_register[i] for i in self.SHOR_PHASE_FLIP_TARGETS):
            self.transpiled_qc.z(q)
        self.insert_syndromes(logical_qubit_index)

    def _logical_y(self, logical_qubit_index: int) -> None:
        """Apply logical Y as logical Z followed by logical X, up to a global phase."""
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in (physical_data_register[0], physical_data_register[1], physical_data_register[2]):
            self.transpiled_qc.x(q)
        for q in (physical_data_register[i] for i in self.SHOR_PHASE_FLIP_TARGETS):
            self.transpiled_qc.z(q)
        self.insert_syndromes(logical_qubit_index)

    def _logical_z(self, logical_qubit_index: int) -> None:
        """Apply logical Z as X on the three qubits of the first block (X_0 X_1 X_2)."""
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in (physical_data_register[0], physical_data_register[1], physical_data_register[2]):
            self.transpiled_qc.x(q)
        self.insert_syndromes(logical_qubit_index)

    def _logical_cx(self, control_logical_qubit_index: int, target_logical_qubit_index: int) -> None:
        """Apply logical CX as physical CX gates with control and target swapped.

        Logical X acts as physical Z in Shor's 9-qubit code, so the physical CX gates must point
        from the target block to the control block.
        """
        control_physical_data_register = self.logical_qubits[control_logical_qubit_index].data
        target_physical_data_register = self.logical_qubits[target_logical_qubit_index].data
        for physical_qubit_index in range(self.BLOCK_SIZE):
            control_qubit = control_physical_data_register[physical_qubit_index]
            target_qubit = target_physical_data_register[physical_qubit_index]
            self.transpiled_qc.cx(target_qubit, control_qubit)

        self.insert_syndromes(control_logical_qubit_index)
        self.insert_syndromes(target_logical_qubit_index)

    def _run_syndrome_cycle(self, qubit: LogicalQubit) -> None:
        """Extract the bit-flip and phase-flip syndromes and apply the corrections."""
        self._extract_bit_flip_syndromes(qubit)
        self._extract_phase_flip_syndromes(qubit)
        self._apply_error_corrections(qubit)

    def _extract_bit_flip_syndromes(self, qubit: LogicalQubit) -> None:
        """Extract bit-flip syndromes for the three blocks."""
        self.transpiled_qc.reset(qubit.bit_flip_syndrome)
        for i in range(self.SHOR_NUM_BLOCKS):
            self.transpiled_qc.compose(
                get_three_qubit_bit_flip_syndrome_extraction_circuit(),
                qubits=qubit.data[i * self.SHOR_BLOCK_SIZE : (i + 1) * self.SHOR_BLOCK_SIZE]
                + qubit.bit_flip_syndrome[i * 2 : (i + 1) * 2],
                inplace=True,
            )

    def _extract_phase_flip_syndromes(self, qubit: LogicalQubit) -> None:
        """Extract phase-flip syndromes across the blocks."""
        self.transpiled_qc.reset(qubit.phase_flip_syndrome)
        self.transpiled_qc.compose(
            get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit(),
            qubits=qubit.data[:] + qubit.phase_flip_syndrome[:],
            inplace=True,
        )

    def _apply_error_corrections(self, qubit: LogicalQubit) -> None:
        """Apply bit-flip and phase-flip error corrections based on syndromes."""
        apply_nine_qubit_shors_code_bit_flip_correction(
            self.transpiled_qc,
            qubit.data,
            qubit.bit_flip_syndrome,
            qubit.bit_flip_measure,
        )

        apply_nine_qubit_shors_code_phase_flip_correction(
            self.transpiled_qc,
            qubit.data,
            qubit.phase_flip_syndrome,
            qubit.phase_flip_measure,
        )
