# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Shor Transpiler for converting standard circuits into fault-tolerant circuits using the 9-qubit Shor code."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import AncillaRegister

# ruff: noqa: PLC2701
#  these functions are reused from the benchmark and they should be extendable i.e. they shouldn't be private
from mqt.bench.benchmarks.shors_nine_qubit_code import (
    _apply_nine_qubit_shors_code_bit_flip_correction,
    _apply_nine_qubit_shors_code_phase_flip_correction,
    _get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit,
    _get_three_qubit_bit_flip_encoding_decoding_circuit,
    _get_three_qubit_bit_flip_syndrome_extraction_circuit,
    _get_three_qubit_phase_flip_encoding_circuit,
)

if TYPE_CHECKING:
    from qiskit.circuit import CircuitInstruction


class ShorTranspiler:
    """A high-level transpiler that encodes a QuantumCircuit using Shor's 9-qubit error correction code."""

    def __init__(self, original_circuit: QuantumCircuit) -> None:
        """Initialize the transpiler with the original QuantumCircuit."""
        self.original_qc = original_circuit
        self.num_logical_qubits = original_circuit.num_qubits
        self.physical_data_registers: list[QuantumRegister] = []
        self.bit_flip_syndromes: list[AncillaRegister] = []
        self.phase_flip_syndromes: list[AncillaRegister] = []
        self.bit_flip_syndrome_measurements: list[ClassicalRegister] = []
        self.phase_flip_syndrome_measurements: list[ClassicalRegister] = []
        self.transpiled_qc = QuantumCircuit()

    def transpile(self) -> QuantumCircuit:
        """Transpile the original circuit to a fault-tolerant circuit using Shor's code."""
        self.encode_qubits()
        self.replace_gates()
        return self.transpiled_qc

    def encode_qubits(self) -> None:
        """Replace each logical qubit with a 9-qubit physical register and apply Shor encoding."""
        all_registers = []
        for logical_qubit_index in range(self.num_logical_qubits):
            physical_data_register = QuantumRegister(9, f"q{logical_qubit_index}")
            bit_flip_syndrome_register = AncillaRegister(6, f"bs{logical_qubit_index}")
            phase_flip_syndrome_register = AncillaRegister(2, f"ps{logical_qubit_index}")
            bit_flip_measurement_register = ClassicalRegister(6, f"bsm{logical_qubit_index}")
            phase_flip_measurement_register = ClassicalRegister(2, f"psm{logical_qubit_index}")

            self.physical_data_registers.append(physical_data_register)
            self.bit_flip_syndromes.append(bit_flip_syndrome_register)
            self.phase_flip_syndromes.append(phase_flip_syndrome_register)
            self.bit_flip_syndrome_measurements.append(bit_flip_measurement_register)
            self.phase_flip_syndrome_measurements.append(phase_flip_measurement_register)

            all_registers.extend([
                physical_data_register,
                bit_flip_syndrome_register,
                phase_flip_syndrome_register,
                bit_flip_measurement_register,
                phase_flip_measurement_register,
            ])

        self.transpiled_qc = QuantumCircuit(*all_registers)
        self.transpiled_qc.name = f"{self.original_qc.name}_shor_encoded"

        # Apply encoding for each logical qubit
        for logical_qubit_index in range(self.num_logical_qubits):
            physical_data_register = self.physical_data_registers[logical_qubit_index]

            # Phase flip encoding on the first qubit of each block
            self.transpiled_qc.compose(
                _get_three_qubit_phase_flip_encoding_circuit(),
                qubits=[physical_data_register[0], physical_data_register[3], physical_data_register[6]],
                inplace=True,
            )

            # Bit flip encoding on each block
            self.transpiled_qc.compose(
                _get_three_qubit_bit_flip_encoding_decoding_circuit(),
                qubits=physical_data_register[:3],
                inplace=True,
            )
            self.transpiled_qc.compose(
                _get_three_qubit_bit_flip_encoding_decoding_circuit(),
                qubits=physical_data_register[3:6],
                inplace=True,
            )
            self.transpiled_qc.compose(
                _get_three_qubit_bit_flip_encoding_decoding_circuit(),
                qubits=physical_data_register[6:9],
                inplace=True,
            )
        self.transpiled_qc.barrier()

    def replace_gates(self) -> None:
        """Scan original circuit and replace gates with logical equivalents."""
        gate_handlers = {
            "barrier": self._handle_barrier,
            "measure": self._handle_measure,
            "h": self._handle_h,
            "x": self._handle_x,
            "z": self._handle_z,
            "s": self._handle_s,
            "cx": self._handle_cx,
            "cz": self._handle_cz,
        }

        for instruction in self.original_qc.data:
            gate_name = instruction.operation.name
            if gate_name in gate_handlers:
                gate_handlers[gate_name](instruction)
            else:
                msg = f"Gate {gate_name} is not supported by ShorTranspiler."
                raise NotImplementedError(msg)

    def _handle_barrier(self, instruction: CircuitInstruction) -> None:
        """Handle barrier instruction."""
        logical_instruction_qubits = instruction.qubits
        involved_physical_data_registers = [
            self.physical_data_registers[self.original_qc.qubits.index(logical_qubit)]
            for logical_qubit in logical_instruction_qubits
        ]
        flattened_physical_qubits = [
            physical_qubit
            for physical_data_register in involved_physical_data_registers
            for physical_qubit in physical_data_register
        ]
        if flattened_physical_qubits:
            self.transpiled_qc.barrier(flattened_physical_qubits)
        else:
            self.transpiled_qc.barrier()

    def _handle_measure(self, instruction: CircuitInstruction) -> None:
        """Handle measure instruction."""
        logical_instruction_qubits = instruction.qubits
        logical_instruction_clbits = instruction.clbits
        logical_qubit_index = self.original_qc.qubits.index(logical_instruction_qubits[0])
        logical_classical_bit_index = self.original_qc.clbits.index(logical_instruction_clbits[0])
        measurement_register_name = f"meas_{logical_qubit_index}_{logical_classical_bit_index}"
        physical_measurement_register = ClassicalRegister(9, measurement_register_name)
        self.transpiled_qc.add_register(physical_measurement_register)

        physical_data_register = self.physical_data_registers[logical_qubit_index]

        # --- Editable and Well-Commented Majority Vote Section ---
        # NOTE: In a physical quantum computer, you would measure the 9 physical qubits
        # into 9 classical bits. Classical post-processing would then compute the
        # majority vote across the 3 bit-flip blocks and then across the phase-flip blocks.
        # Here, we perform the 9 physical measurements.
        self.transpiled_qc.measure(physical_data_register, physical_measurement_register)
        
        # A classical post-processing function for majority vote could look like:
        #
        # def classical_majority_vote(bitstring: str) -> str:
        #     '''Computes the logical bit value from the 9 physical bit measurements.'''
        #     # bitstring is 9 bits: b8 b7 b6 b5 b4 b3 b2 b1 b0
        #     blocks = [bitstring[6:9], bitstring[3:6], bitstring[0:3]]
        #     block_votes = [1 if block.count('1') > 1 else 0 for block in blocks]
        #     logical_bit = 1 if sum(block_votes) > 1 else 0
        #     return str(logical_bit)
        # ---------------------------------------------------------

    def _handle_h(self, instruction: CircuitInstruction) -> None:
        """Handle Hadamard instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]
        for physical_qubit_index in range(9):
            self.transpiled_qc.h(physical_data_register[physical_qubit_index])
        # The Hadamard gate is not completely transversal for Shor's code.
        # It needs to be followed by a swap that transposes the 9 qubits.
        self.transpiled_qc.swap(physical_data_register[1], physical_data_register[3])
        self.transpiled_qc.swap(physical_data_register[2], physical_data_register[6])
        self.transpiled_qc.swap(physical_data_register[5], physical_data_register[7])
        self.insert_syndromes(logical_qubit_index)

    def _handle_x(self, instruction: CircuitInstruction) -> None:
        """Handle X instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]
        # Explanation: In Shor's 9-qubit code, the logical states |0>_L and |1>_L are eigenstates of
        # transversal X and Z with eigenvalues swapped relative to single physical qubits.
        # Applying a physical Z to all 9 qubits transforms |0>_L to |1>_L (and vice versa), which acts
        # as a logical X gate. Therefore, to implement logical X, we apply physical Z transversally.
        for physical_qubit_index in range(9):
            self.transpiled_qc.z(physical_data_register[physical_qubit_index])
        self.insert_syndromes(logical_qubit_index)

    def _handle_z(self, instruction: CircuitInstruction) -> None:
        """Handle Z instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]
        # Explanation: Conversely, applying a physical X to all 9 qubits imparts a -1 phase to |1>_L
        # while leaving |0>_L unchanged. This acts as a logical Z gate. Therefore, to implement
        # logical Z, we apply physical X transversally.
        for physical_qubit_index in range(9):
            self.transpiled_qc.x(physical_data_register[physical_qubit_index])
        self.insert_syndromes(logical_qubit_index)

    def _handle_s(self, instruction: CircuitInstruction) -> None:
        """Handle S instruction."""
        # Explanation: A purely transversal physical S gate destroys the superposition in Shor's 9-qubit code
        # and is not fault-tolerant. Universal fault-tolerance requires non-transversal techniques such as
        # magic state injection to properly implement the logical phase gate (S).
        msg = "Logical S gate is not fault-tolerant transversally in Shor's code and requires magic state injection."
        raise NotImplementedError(msg)

    def _handle_cx(self, instruction: CircuitInstruction) -> None:
        """Handle CX instruction."""
        control_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        target_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[1])
        control_physical_data_register = self.physical_data_registers[control_logical_qubit_index]
        target_physical_data_register = self.physical_data_registers[target_logical_qubit_index]
        for physical_qubit_index in range(9):
            self.transpiled_qc.cx(
                control_physical_data_register[physical_qubit_index],
                target_physical_data_register[physical_qubit_index],
            )
        self.insert_syndromes(control_logical_qubit_index)
        self.insert_syndromes(target_logical_qubit_index)
# it should use the hadamards with cnots 
    def _handle_cz(self, instruction: CircuitInstruction) -> None:
        """Handle CZ instruction."""
        control_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        target_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[1])
        control_physical_data_register = self.physical_data_registers[control_logical_qubit_index]
        target_physical_data_register = self.physical_data_registers[target_logical_qubit_index]
        for physical_qubit_index in range(9):
            self.transpiled_qc.cz(
                control_physical_data_register[physical_qubit_index],
                target_physical_data_register[physical_qubit_index],
            )
        self.insert_syndromes(control_logical_qubit_index)
        self.insert_syndromes(target_logical_qubit_index)
#TODO: Review and verify it works
    def insert_syndromes(self, logical_qubit_index: int) -> None:
        """Automate the insertion of the measurement and correction cycles."""
        physical_data_register = self.physical_data_registers[logical_qubit_index]
        bit_flip_syndrome_register = self.bit_flip_syndromes[logical_qubit_index]
        phase_flip_syndrome_register = self.phase_flip_syndromes[logical_qubit_index]
        bit_flip_measurement_register = self.bit_flip_syndrome_measurements[logical_qubit_index]
        phase_flip_measurement_register = self.phase_flip_syndrome_measurements[logical_qubit_index]

        self.transpiled_qc.barrier()

        # Bit-flip syndrome extraction
        self.transpiled_qc.compose(
            _get_three_qubit_bit_flip_syndrome_extraction_circuit(),
            qubits=physical_data_register[:3] + bit_flip_syndrome_register[:2],
            inplace=True,
        )
        self.transpiled_qc.compose(
            _get_three_qubit_bit_flip_syndrome_extraction_circuit(),
            qubits=physical_data_register[3:6] + bit_flip_syndrome_register[2:4],
            inplace=True,
        )
        self.transpiled_qc.compose(
            _get_three_qubit_bit_flip_syndrome_extraction_circuit(),
            qubits=physical_data_register[6:9] + bit_flip_syndrome_register[4:6],
            inplace=True,
        )

        self.transpiled_qc.barrier()

        # Phase-flip syndrome extraction
        self.transpiled_qc.compose(
            _get_nine_qubit_shors_code_phase_flip_syndrome_extraction_circuit(),
            qubits=physical_data_register[:] + phase_flip_syndrome_register[:],
            inplace=True,
        )

        self.transpiled_qc.barrier()

        # Error correction
        _apply_nine_qubit_shors_code_bit_flip_correction(
            self.transpiled_qc,
            physical_data_register,
            bit_flip_syndrome_register,
            bit_flip_measurement_register,
        )
        self.transpiled_qc.barrier()
        _apply_nine_qubit_shors_code_phase_flip_correction(
            self.transpiled_qc,
            physical_data_register,
            phase_flip_syndrome_register,
            phase_flip_measurement_register,
        )
        self.transpiled_qc.barrier()
