# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Shor Transpiler for converting standard circuits into fault-tolerant circuits using the 9-qubit Shor code."""

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
    """A high-level transpiler that encodes a QuantumCircuit using Shor's 9-qubit error correction code.

    Only gates whose logical realization is not a plain transversal application of a single
    physical gate need a dedicated handler here (``id`` is the only gate transversal in the
    strict sense used by :class:`ECTranspiler`). Every other unhandled gate in
    :attr:`TARGET_GATE_SET` -- notably ``t``, ``tdg``, and ``h`` (whose textbook realization via
    physical Hadamards and block-transposing SWAPs is not fault-tolerant for the plain 9-qubit
    Shor code) -- is automatically realized as an opaque, ideal logical gadget.
    """

    # Constants for the Shor 9-qubit code structure
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
        """Apply Shor 9-qubit encoding to a physical data register."""
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
        """Apply Shor 9-qubit decoding to a physical data register."""
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
        """Apply Transversal logical X.

        In Shor's code, a logical X acts like a global physical Z across the three
        blocks. Since Z on one qubit of a block flips the entire block's phase,
        applying one Z per block (Z_0 Z_3 Z_6) transversally achieves logical X.
        """
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in (physical_data_register[i] for i in self.SHOR_PHASE_FLIP_TARGETS):
            self.transpiled_qc.z(q)
        self.insert_syndromes(logical_qubit_index)

    def _logical_y(self, logical_qubit_index: int) -> None:
        """Apply transversal logical Y.

        Since Y = iXZ (up to global phase), logical Y is realized by applying the
        physical operations for logical Z and logical X. Logical Z acts as X on the
        three qubits of the first block (X_0 X_1 X_2), and logical X acts as Z on the
        first qubit of each block (Z_0 Z_3 Z_6). The global phase i is unobservable.
        """
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in (physical_data_register[0], physical_data_register[1], physical_data_register[2]):
            self.transpiled_qc.x(q)
        for q in (physical_data_register[i] for i in self.SHOR_PHASE_FLIP_TARGETS):
            self.transpiled_qc.z(q)
        self.insert_syndromes(logical_qubit_index)

    def _logical_z(self, logical_qubit_index: int) -> None:
        """Apply Transversal logical Z.

        Applying X to the three qubits of a single block (e.g. X_0 X_1 X_2) maps
        |000> to |111>, effectively giving diag(+1,-1) on the logical subspace.
        """
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in (physical_data_register[0], physical_data_register[1], physical_data_register[2]):
            self.transpiled_qc.x(q)
        self.insert_syndromes(logical_qubit_index)

    def _logical_cx(self, control_logical_qubit_index: int, target_logical_qubit_index: int) -> None:
        """Apply transversal logical CX.

        Because the Shor logical operators X_L and Z_L have interchanged physical basis mapping
        compared to typical codes, the physical CX role is inverted: control and target are
        swapped at the physical level to construct a logical CX.
        """
        control_physical_data_register = self.logical_qubits[control_logical_qubit_index].data
        target_physical_data_register = self.logical_qubits[target_logical_qubit_index].data
        for physical_qubit_index in range(self.BLOCK_SIZE):
            # Physical control/target are swapped relative to logical
            control_qubit = control_physical_data_register[physical_qubit_index]
            target_qubit = target_physical_data_register[physical_qubit_index]
            self.transpiled_qc.cx(target_qubit, control_qubit)

        self.insert_syndromes(control_logical_qubit_index)
        self.insert_syndromes(target_logical_qubit_index)

    def _run_syndrome_cycle(self, qubit: LogicalQubit) -> None:
        """Run the Shor code's bit-flip and phase-flip syndrome extraction and correction cycle.

        Performs three stages of error correction on the Shor block belonging to ``qubit``:

        1. **Bit-flip syndrome extraction**: Each of the three 3-qubit blocks is checked independently.
        Per block, two ancillas record the stabilizer parities (Z_i Z_j checks),
        localizing an X error to one of the block's three qubits.
        2. **Phase-flip syndrome extraction**: The parities between the three blocks
        (X-type stabilizers spanning six qubits each) are extracted,
        localizing a single Z error to one of the three blocks.
        3. **Correction**: The ancillas are measured into the corresponding classical syndrome registers,
        and X and Z corrections are applied to the identified data qubit.

        Ancilla registers are reset to |0> at the start of each cycle.
        """
        self._extract_bit_flip_syndromes(qubit)
        self._extract_phase_flip_syndromes(qubit)
        self._apply_error_corrections(qubit)

    def _extract_bit_flip_syndromes(self, qubit: LogicalQubit) -> None:
        """Extract bit-flip syndromes for the three blocks."""
        if qubit.bit_flip_syndrome is None:
            msg = "Bit-flip syndrome register is missing or not initialized."
            raise ValueError(msg)

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
        if qubit.phase_flip_syndrome is None:
            msg = "Phase-flip syndrome register is missing or not initialized."
            raise ValueError(msg)

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
