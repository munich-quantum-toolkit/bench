# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Shor Transpiler for converting standard circuits into fault-tolerant circuits using the 9-qubit Shor code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit import AncillaRegister, Instruction

# these functions are reused from the benchmark and they should be extendable therefore they were moved into a dedicated block
from mqt.bench.components.shor_circuit_components import (
    apply_nine_qubit_shors_code_bit_flip_correction,
    apply_nine_qubit_shors_code_phase_flip_correction,
    get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit,
    get_three_qubit_bit_flip_encoding_decoding_circuit,
    get_three_qubit_bit_flip_syndrome_extraction_circuit,
    get_three_qubit_phase_flip_encoding_circuit,
)

if TYPE_CHECKING:
    from collections.abc import Callable

# Constants for the Shor 9-qubit code structure
SHOR_TOTAL_QUBITS = 9
SHOR_BLOCK_SIZE = 3
SHOR_NUM_BLOCKS = 3
SHOR_PHASE_FLIP_TARGETS = [0, 3, 6]


@dataclass
class ShorLogicalQubit:
    """Encapsulates the physical registers representing a single Shor logical qubit."""

    data: QuantumRegister
    bit_flip_syndrome: AncillaRegister | None = None
    phase_flip_syndrome: AncillaRegister | None = None
    bit_flip_measure: ClassicalRegister | None = None
    phase_flip_measure: ClassicalRegister | None = None

    def get_all_registers(self) -> list:
        """Return all active registers for this logical qubit."""
        regs = [self.data]
        if self.bit_flip_syndrome:
            regs.extend(
                reg
                for reg in [
                    self.bit_flip_syndrome,
                    self.phase_flip_syndrome,
                    self.bit_flip_measure,
                    self.phase_flip_measure,
                ]
                if reg is not None
            )
        return regs


class ShorTranspiler:
    """A high-level transpiler that encodes a QuantumCircuit using Shor's 9-qubit error correction code."""

    def __init__(self, original_circuit: QuantumCircuit, *, add_syndromes: bool = True) -> None:
        """Initialize the transpiler with the original QuantumCircuit.

        Args:
            original_circuit: Original circuit to transpile using Shor's code.
            add_syndromes: Whether to insert syndrome extraction and correction cycles.
        """
        self.original_qc = original_circuit
        self.num_logical_qubits = original_circuit.num_qubits
        self.add_syndromes = add_syndromes
        self.logical_qubits: list[ShorLogicalQubit] = []
        self.s_gate_count = 0
        self.t_gate_count = 0
        self.transpiled_qc = QuantumCircuit()

        # We need this for backwards compatibility with the testing suite
        self.physical_data_registers: list[QuantumRegister] = []

    def transpile(self) -> QuantumCircuit:
        """Transpile the original circuit to a fault-tolerant circuit using Shor's code.

        High-level Qiskit instructions such as ``QFTGate`` are first decomposed
        into the supported basis gates. For QFT, this decomposition currently
        uses ``approximation_degree=0.95``, so encoded QFT circuits are
        approximate rather than exact.

        Returns:
             The transpiled fault-tolerant circuit.
        """
        self.original_qc = transpile(
            self.original_qc,
            basis_gates=["id", "h", "x", "y", "z", "cx", "swap", "dcx", "t", "tdg"],
            optimization_level=3,
            approximation_degree=0.95,
            seed_transpiler=10,
        )

        self.encode_qubits()
        self.replace_gates()
        return self.transpiled_qc

    def encode_qubits(self) -> None:
        """Replace each logical qubit with a 9-qubit physical register and apply Shor encoding."""
        all_registers = []
        for i in range(self.num_logical_qubits):
            data_reg = QuantumRegister(SHOR_TOTAL_QUBITS, f"q{i}")
            self.physical_data_registers.append(data_reg)

            if self.add_syndromes:
                logical_qubit = ShorLogicalQubit(
                    data=data_reg,
                    bit_flip_syndrome=AncillaRegister(6, f"bs{i}"),
                    phase_flip_syndrome=AncillaRegister(2, f"ps{i}"),
                    bit_flip_measure=ClassicalRegister(6, f"bsm{i}"),
                    phase_flip_measure=ClassicalRegister(2, f"psm{i}"),
                )
            else:
                logical_qubit = ShorLogicalQubit(data=data_reg)

            self.logical_qubits.append(logical_qubit)
            all_registers.extend(logical_qubit.get_all_registers())

        self.transpiled_qc = QuantumCircuit(*all_registers)
        self.transpiled_qc.name = f"{self.original_qc.name}_shor_encoded"

        # Apply encoding for each logical qubit
        for logical_qubit in self.logical_qubits:
            self._apply_shor_encoding(self.transpiled_qc, logical_qubit.data)

    @staticmethod
    def _apply_shor_encoding(qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply Shor 9-qubit encoding to a physical data register."""
        # Phase flip encoding on the first qubit of each block
        qc.compose(
            get_three_qubit_phase_flip_encoding_circuit(),
            qubits=[physical_data_register[i] for i in SHOR_PHASE_FLIP_TARGETS],
            inplace=True,
        )

        # Bit flip encoding on each block
        for i in range(SHOR_NUM_BLOCKS):
            qc.compose(
                get_three_qubit_bit_flip_encoding_decoding_circuit(),
                qubits=physical_data_register[i * SHOR_BLOCK_SIZE : (i + 1) * SHOR_BLOCK_SIZE],
                inplace=True,
            )

    @staticmethod
    def _apply_shor_decoding(qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply Shor 9-qubit decoding to a physical data register."""
        for i in range(SHOR_NUM_BLOCKS):
            qc.compose(
                get_three_qubit_bit_flip_encoding_decoding_circuit().inverse(),
                qubits=physical_data_register[i * SHOR_BLOCK_SIZE : (i + 1) * SHOR_BLOCK_SIZE],
                inplace=True,
            )
        qc.compose(
            get_three_qubit_phase_flip_encoding_circuit().inverse(),
            qubits=[physical_data_register[i] for i in SHOR_PHASE_FLIP_TARGETS],
            inplace=True,
        )

    def replace_gates(self) -> None:
        """Scan the original circuit and replace gates with logical equivalents.

        High-level gates are normalized before logical encoding. In particular,
        ``QFTGate`` instructions are transpiled to the supported
        ``["h", "x", "z", "s", "t", "cx", "cz"]`` basis with
        ``approximation_degree=0.95``. This means QFT instructions are encoded
        as approximate circuits rather than exact QFT implementations.
        """
        # Circuit-wide transpile to the supported basis gates
        for instruction in self.original_qc.data:
            gate_name = instruction.operation.name
            handler_name = f"_logical_{gate_name}"

            if not hasattr(self, handler_name):
                msg = f"Gate {gate_name} is not supported by ShorTranspiler."
                raise NotImplementedError(msg)

            handler = getattr(self, handler_name)
            logical_qubit_indices = [self.original_qc.qubits.index(q) for q in instruction.qubits]
            logical_clbit_indices = [self.original_qc.clbits.index(c) for c in instruction.clbits]

            if gate_name == "barrier":
                handler(logical_qubit_indices)
            elif gate_name == "measure":
                handler(logical_qubit_indices[0], logical_clbit_indices[0])
            elif gate_name in ["cx", "cz", "swap", "dcx"]:
                handler(logical_qubit_indices[0], logical_qubit_indices[1])
            else:
                handler(logical_qubit_indices[0])

    def _logical_barrier(self, logical_qubit_indices: list[int]) -> None:
        """Apply logical barrier across the specified physical qubits."""
        involved_physical_data_registers = [self.logical_qubits[idx].data for idx in logical_qubit_indices]
        flattened_physical_qubits = [
            physical_qubit
            for physical_data_register in involved_physical_data_registers
            for physical_qubit in physical_data_register
        ]
        if flattened_physical_qubits:
            self.transpiled_qc.barrier(flattened_physical_qubits)
        else:
            self.transpiled_qc.barrier()

    def _logical_measure(self, logical_qubit_index: int, logical_classical_bit_index: int) -> None:
        """Apply logical measurement mapping to 9 physical measurements.

        Classical post-processing would compute the majority vote across the 3 bit-flip
        blocks and then across the phase-flip blocks to extract the logical value.
        """
        ## decode
        self._apply_shor_decoding(self.transpiled_qc, self.logical_qubits[logical_qubit_index].data)
        measurement_register_name = f"meas_{logical_qubit_index}_{logical_classical_bit_index}"
        physical_measurement_register = ClassicalRegister(1, measurement_register_name)
        self.transpiled_qc.add_register(physical_measurement_register)

        physical_data_register = self.logical_qubits[logical_qubit_index].data
        self.transpiled_qc.measure(physical_data_register[0], physical_measurement_register[0])

    def _logical_id(self, logical_qubit_index: int) -> None:
        """Apply Transversal logical Id.

        In Shor's code, a logical Id acts like a global physical No-Op across all data
        qubits.
        """
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in physical_data_register:
            self.transpiled_qc.id(q)
        self.insert_syndromes(logical_qubit_index)

    def _logical_h(self, logical_qubit_index: int) -> None:
        """Apply logical Hadamard.

        The Hadamard gate is not completely transversal for Shor's code. It requires
        applying physical H gates followed by SWAPs that transpose the 9-qubit blocks.
        """
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for physical_qubit_index in range(SHOR_TOTAL_QUBITS):
            self.transpiled_qc.h(physical_data_register[physical_qubit_index])
        # The Hadamard gate is not completely transversal for Shor's code.
        # It needs to be followed by a swap that transposes the 9 qubits.
        self.transpiled_qc.swap(physical_data_register[1], physical_data_register[3])
        self.transpiled_qc.swap(physical_data_register[2], physical_data_register[6])
        self.transpiled_qc.swap(physical_data_register[5], physical_data_register[7])
        self.insert_syndromes(logical_qubit_index)

    def _logical_x(self, logical_qubit_index: int) -> None:
        """Apply Transversal logical X.

        In Shor's code, a logical X acts like a global physical Z across the three
        blocks. Since Z on one qubit of a block flips the entire block's phase,
        applying one Z per block (Z_0 Z_3 Z_6) transversally achieves logical X.
        """
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        for q in (physical_data_register[i] for i in SHOR_PHASE_FLIP_TARGETS):
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
        for q in (physical_data_register[i] for i in SHOR_PHASE_FLIP_TARGETS):
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

    def _apply_teleportation_gadget(
        self,
        logical_qubit_index: int,
        phase: float,
        ancilla_name: str,
        measure_name: str,
        correction_callback: Callable,
    ) -> None:
        """Apply a magic state gate teleportation gadget (used for non-transversal S and T gates)."""
        ancilla_register = QuantumRegister(SHOR_TOTAL_QUBITS, ancilla_name)
        creg = ClassicalRegister(1, measure_name)
        self.transpiled_qc.add_register(ancilla_register)
        self.transpiled_qc.add_register(creg)

        physical_data_register = self.logical_qubits[logical_qubit_index].data

        # Prepare magic state: H -> P(phase) -> Encode
        self._prepare_magic(self.transpiled_qc, ancilla_register, phase)

        # Transversal logical CNOT
        self._apply_logical_cx(physical_data_register, ancilla_register)

        # Decode and measure ancilla in logical Z basis
        self._apply_shor_decoding(self.transpiled_qc, ancilla_register)
        self.transpiled_qc.measure(ancilla_register[0], creg[0])

        # Apply conditional correction based on the measurement outcome
        with self.transpiled_qc.if_test((creg[0], 1)):
            correction_callback()

        self.insert_syndromes(logical_qubit_index)

    def _logical_t(self, logical_qubit_index: int) -> None:
        """Apply logical T via magic state injection."""
        self.t_gate_count += 1
        t_magic_inst = Instruction(
            name="shor_logical_t_magic_state_injection",
            num_qubits=9,
            num_clbits=0,
            params=[],
        )
        self.transpiled_qc.append(t_magic_inst, self.logical_qubits[logical_qubit_index].data)
        self.insert_syndromes(logical_qubit_index)

    def _logical_tdg(self, logical_qubit_index: int) -> None:
        """Apply logical T-dagger via magic state injection."""
        self.t_gate_count += 1
        tdg_magic_inst = Instruction(
            name="shor_logical_t_magic_state_injection_dg",
            num_qubits=9,
            num_clbits=0,
            params=[],
        )
        self.transpiled_qc.append(tdg_magic_inst, self.logical_qubits[logical_qubit_index].data)
        self.insert_syndromes(logical_qubit_index)

    @staticmethod
    def _prepare_magic(qc: QuantumCircuit, physical_ancilla_register: QuantumRegister, phase: float) -> None:
        """Encode a magic state (|0> + e^{i*phase}|1>)/sqrt2 into a physical register."""
        qc.h(physical_ancilla_register[0])
        qc.p(phase, physical_ancilla_register[0])
        ShorTranspiler._apply_shor_encoding(qc, physical_ancilla_register)

    def _apply_logical_cx(self, logical_control: QuantumRegister, logical_target: QuantumRegister) -> None:
        """Apply transversal logical CX between two physical registers.

        Note: Due to Shor code structure, physical CX control/target are inverted.
        """
        for physical_qubit_index in range(SHOR_TOTAL_QUBITS):
            # Physical control/target are swapped relative to logical
            self.transpiled_qc.cx(logical_target[physical_qubit_index], logical_control[physical_qubit_index])

    def _logical_cx(self, control_logical_qubit_index: int, target_logical_qubit_index: int) -> None:
        """Apply transversal logical CX.

        Because the Shor logical operators X_L and Z_L have interchanged physical basis mapping
        compared to typical codes, the physical CX role is inverted: control and target are
        swapped at the physical level to construct a logical CX.
        """
        control_physical_data_register = self.logical_qubits[control_logical_qubit_index].data
        target_physical_data_register = self.logical_qubits[target_logical_qubit_index].data
        self._apply_logical_cx(control_physical_data_register, target_physical_data_register)

        self.insert_syndromes(control_logical_qubit_index)
        self.insert_syndromes(target_logical_qubit_index)

    def _logical_dcx(self, control_logical_qubit_index: int, target_logical_qubit_index: int) -> None:
        """Apply logical DCX (double-CNOT), implemented as two logical CX gates.

        DCX(a, b) applies CX(a, b) followed by CX(b, a). Matching Qiskit's DCXGate
        convention, the first qubit is the control of the first CX and the target of
        the second. Each logical CX is transversal, so the composed DCX is transversal.
        """
        self._logical_cx(control_logical_qubit_index, target_logical_qubit_index)
        self._logical_cx(target_logical_qubit_index, control_logical_qubit_index)

    def _logical_swap(self, first_logical_qubit_index: int, second_logical_qubit_index: int) -> None:
        """Apply logical SWAP (implemented as three alternating logical CX gates).

        SWAP(a, b) = CX(a, b) . CX(b, a) . CX(a, b). Each logical CX is transversal,
        so the composed SWAP is transversal as well. The individual _logical_cx calls
        already insert their own syndrome extraction cycles.
        """
        self._logical_cx(first_logical_qubit_index, second_logical_qubit_index)
        self._logical_cx(second_logical_qubit_index, first_logical_qubit_index)
        self._logical_cx(first_logical_qubit_index, second_logical_qubit_index)

    def insert_syndromes(self, logical_qubit_index: int) -> None:
        """Automate the insertion of bit-flip and phase-flip error correction cycles."""
        if not self.add_syndromes:
            return

        qubit = self.logical_qubits[logical_qubit_index]

        self._extract_bit_flip_syndromes(qubit)

        self._extract_phase_flip_syndromes(qubit)

        self._apply_error_corrections(qubit)

    def _extract_bit_flip_syndromes(self, qubit: ShorLogicalQubit) -> None:
        """Extract bit-flip syndromes for the three blocks."""
        if qubit.bit_flip_syndrome is None:
            msg = "Bit-flip syndrome register is missing or not initialized."
            raise ValueError(msg)

        self.transpiled_qc.reset(qubit.bit_flip_syndrome)
        for i in range(SHOR_NUM_BLOCKS):
            self.transpiled_qc.compose(
                get_three_qubit_bit_flip_syndrome_extraction_circuit(),
                qubits=qubit.data[i * SHOR_BLOCK_SIZE : (i + 1) * SHOR_BLOCK_SIZE]
                + qubit.bit_flip_syndrome[i * 2 : (i + 1) * 2],
                inplace=True,
            )

    def _extract_phase_flip_syndromes(self, qubit: ShorLogicalQubit) -> None:
        """Extract phase-flip syndromes across the blocks."""
        if qubit.phase_flip_syndrome is None:
            msg = "Bit-flip syndrome register is missing or not initialized."
            raise ValueError(msg)

        self.transpiled_qc.reset(qubit.phase_flip_syndrome)
        self.transpiled_qc.compose(
            get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit(),
            qubits=qubit.data[:] + qubit.phase_flip_syndrome[:],
            inplace=True,
        )

    def _apply_error_corrections(self, qubit: ShorLogicalQubit) -> None:
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
