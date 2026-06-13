# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Steane Transpiler for converting standard circuits into fault-tolerant circuits using the 7-qubit Steane code."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit import AncillaRegister

from mqt.bench.components.steane_circuit_components import (
    apply_seven_qubit_steane_code_correction,
    get_seven_qubit_steane_code_decoding_circuit,
    get_seven_qubit_steane_code_encoding_circuit,
    get_seven_qubit_steane_code_syndrome_extraction_circuit,
)

if TYPE_CHECKING:
    from qiskit.circuit import CircuitInstruction


class SteaneTranspiler:
    """A high-level transpiler that encodes a QuantumCircuit using Steane's 7-qubit error correction code."""

    def __init__(self, original_circuit: QuantumCircuit, add_syndromes: bool = True) -> None:
        """Initialize the transpiler with the original QuantumCircuit."""
        self.original_qc = original_circuit
        self.num_logical_qubits = original_circuit.num_qubits
        self.physical_data_registers: list[QuantumRegister] = []
        self.bit_flip_syndromes: list[AncillaRegister] = []
        self.phase_flip_syndromes: list[AncillaRegister] = []
        self.bit_flip_syndrome_measurements: list[ClassicalRegister] = []
        self.phase_flip_syndrome_measurements: list[ClassicalRegister] = []
        # self.logical_qubit_measurements: list[ClassicalRegister] = []
        self.add_syndromes = add_syndromes
        self.t_gate_count = 0
        self.transpiled_qc = QuantumCircuit()
        self.gate_handlers = {
            "barrier": self._handle_barrier,
            "measure": self._handle_measure,
            "h": self._handle_h,
            "x": self._handle_x,
            "z": self._handle_z,
            "s": self._handle_s,
            "cx": self._handle_cx,
            "cz": self._handle_cz,
            "t": self._handle_t,
        }

    def transpile(self) -> QuantumCircuit:
        """Transpile the original circuit to a fault-tolerant circuit using Steane's code."""
        self.encode_qubits()
        self.replace_gates()
        return self.transpiled_qc

    def encode_qubits(self) -> None:
        """Replace each logical qubit with a 7-qubit physical register and apply Steane encoding."""
        all_registers = []
        for logical_qubit_index in range(self.num_logical_qubits):
            # use another name as logical_qubit
            physical_data_register = QuantumRegister(7, f"q{logical_qubit_index}")
            bit_flip_syndrome_register = AncillaRegister(3, f"bs{logical_qubit_index}")
            phase_flip_syndrome_register = AncillaRegister(3, f"ps{logical_qubit_index}")
            bit_flip_measurement_register = ClassicalRegister(3, f"bsm{logical_qubit_index}")
            phase_flip_measurement_register = ClassicalRegister(3, f"psm{logical_qubit_index}")
            # logical_qubit_measurement_register = ClassicalRegister(1, f"logical_meas{logical_qubit_index}")

            self.physical_data_registers.append(physical_data_register)
            self.bit_flip_syndromes.append(bit_flip_syndrome_register)
            self.phase_flip_syndromes.append(phase_flip_syndrome_register)
            self.bit_flip_syndrome_measurements.append(bit_flip_measurement_register)
            self.phase_flip_syndrome_measurements.append(phase_flip_measurement_register)
            # self.logical_qubit_measurements.append(logical_qubit_measurement_register)

            all_registers.extend([
                physical_data_register,
                bit_flip_syndrome_register,
                phase_flip_syndrome_register,
                bit_flip_measurement_register,
                phase_flip_measurement_register,
                # logical_qubit_measurement_register
            ])

        self.transpiled_qc = QuantumCircuit(*all_registers)
        self.transpiled_qc.name = f"{self.original_qc.name}_steane_encoded"

        # Apply encoding for each logical qubit
        for logical_qubit_index in range(self.num_logical_qubits):
            physical_data_register = self.physical_data_registers[logical_qubit_index]

            # Phase flip encoding on the first qubit of each block
            self.transpiled_qc.compose(
                get_seven_qubit_steane_code_encoding_circuit(),
                qubits=physical_data_register[:],
                inplace=True,
            )
        self.transpiled_qc.barrier(label="Encoding")

    def decode_qubits(self) -> None:
        """Apply Steane 7-qubit decoding to each logical qubit."""
        self.transpiled_qc.barrier()
        for logical_qubit_index in range(self.num_logical_qubits):
            physical_data_register = self.physical_data_registers[logical_qubit_index]
            self.transpiled_qc.compose(
                get_seven_qubit_steane_code_decoding_circuit(), qubits=physical_data_register[:], inplace=True
            )
        self.transpiled_qc.barrier()

    def replace_gates(self) -> None:
        """Scan original circuit and replace gates with logical equivalents."""
        # Firstly, expand high level gates, such as QFTGate()
        normalized = QuantumCircuit(*self.original_qc.qregs, *self.original_qc.cregs)
        for instruction in self.original_qc.data:
            gate_name = instruction.operation.name

            if gate_name == "qft":
                tmp = QuantumCircuit(len(instruction.qubits))
                tmp.append(instruction.operation, range(len(instruction.qubits)))

                tmp = transpile(
                    tmp,
                    basis_gates=["h", "x", "z", "s", "t", "cx", "cz"],
                    optimization_level=3,
                    approximation_degree=0.95,
                )

                normalized.compose(
                    tmp,
                    qubits=list(instruction.qubits),
                    inplace=True,
                )

            else:
                normalized.append(
                    instruction.operation,
                    instruction.qubits,
                    instruction.clbits,
                )

        self.original_qc = normalized

        for instruction in self.original_qc.data:
            gate_name = instruction.operation.name
            if gate_name in self.gate_handlers:
                self.gate_handlers[gate_name](instruction)
            else:
                msg = f"Gate {gate_name} is not supported by SteaneTranspiler."
                raise NotImplementedError(msg)

    def _handle_barrier(self, instruction: CircuitInstruction) -> None:
        """Handle barrier instruction."""
        barrier_register = []
        for i in range(len(instruction.qubits)):
            physical_data_register = self.physical_data_registers[i]
            bit_flip_syndromes_register = self.bit_flip_syndromes[i]
            phase_flip_syndromes_register = self.phase_flip_syndromes[i]
            barrier_register.extend([
                physical_data_register,
                bit_flip_syndromes_register,
                phase_flip_syndromes_register,
            ])
        self.transpiled_qc.barrier(*barrier_register, label="Barrier")

    def _handle_measure(self, instruction: CircuitInstruction) -> None:
        """Handle measure instruction."""
        # TODO: consider measure_all(), because of new meas register everything goes wrong

        for q, c in zip(instruction.qubits, instruction.clbits, strict=False):
            logical_qubit_index = self.original_qc.qubits.index(q)
            logical_classical_bit_index = self.original_qc.clbits.index(c)

            self.transpiled_qc.compose(
                get_seven_qubit_steane_code_decoding_circuit(),
                qubits=self.physical_data_registers[logical_qubit_index],
                inplace=True,
            )

            measurement_register_name = f"meas_{logical_qubit_index}_{logical_classical_bit_index}"
            physical_measurement_register = ClassicalRegister(1, measurement_register_name)
            self.transpiled_qc.add_register(physical_measurement_register)

            physical_data_register = self.physical_data_registers[logical_qubit_index][0]
            self.transpiled_qc.measure(physical_data_register, physical_measurement_register)

            # self.transpiled_qc.measure(self.physical_data_registers[logical_qubit_index][0],
            #                           self.logical_qubit_measurements[logical_classical_bit_index])

            self.transpiled_qc.barrier(label=f"Measurement {logical_qubit_index}")

    def _handle_h(self, instruction: CircuitInstruction) -> None:
        """Handle Hadamard instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]

        self.transpiled_qc.h(physical_data_register)

        self.transpiled_qc.barrier(label=f"H {logical_qubit_index}")
        if self.add_syndromes:
            self.insert_syndromes(logical_qubit_index)

    def _handle_x(self, instruction: CircuitInstruction) -> None:
        """Handle X instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]

        self.transpiled_qc.x(physical_data_register)

        self.transpiled_qc.barrier(label=f"X {logical_qubit_index}")
        if self.add_syndromes:
            self.insert_syndromes(logical_qubit_index)

    def _handle_z(self, instruction: CircuitInstruction) -> None:
        """Handle Z instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]

        self.transpiled_qc.z(physical_data_register)

        self.transpiled_qc.barrier(label=f"Z {logical_qubit_index}")
        if self.add_syndromes:
            self.insert_syndromes(logical_qubit_index)

    def _handle_s(self, instruction: CircuitInstruction) -> None:
        """Handle S instruction."""
        # S Made cia SDG
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]

        self.transpiled_qc.sdg(physical_data_register)

        self.transpiled_qc.barrier(label=f"S {logical_qubit_index}")
        if self.add_syndromes:
            self.insert_syndromes(logical_qubit_index)

    def _handle_t(self, instruction: CircuitInstruction) -> None:
        """Handle T instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]

        t_ancilla_register = AncillaRegister(7, f"t{self.t_gate_count}")
        self.t_gate_count += 1
        t_test_register = ClassicalRegister(1)

        self.transpiled_qc.add_register(t_ancilla_register)
        self.transpiled_qc.add_register(t_test_register)

        # make ket 0 L
        self.transpiled_qc.compose(
            get_seven_qubit_steane_code_encoding_circuit(),
            qubits=t_ancilla_register[:],
            inplace=True,
        )

        # make ket + L (Applying H L)
        self.transpiled_qc.h(t_ancilla_register)

        # apply physical t gates
        self.transpiled_qc.t(t_ancilla_register)

        # logical cnot from data to ancilla
        self.transpiled_qc.cx(physical_data_register, t_ancilla_register)

        # made logical measurement
        self.transpiled_qc.compose(
            get_seven_qubit_steane_code_decoding_circuit(), qubits=t_ancilla_register, inplace=True
        )
        self.transpiled_qc.measure(t_ancilla_register[0], t_test_register[0])

        # Think about whether need to add error correction after these logical gates

        # apply if_test
        with self.transpiled_qc.if_test((t_test_register[0], 1)):
            self.transpiled_qc.sdg(physical_data_register)

        self.transpiled_qc.barrier(label=f"T {logical_qubit_index}")
        if self.add_syndromes:
            self.insert_syndromes(logical_qubit_index)

    def _handle_cx(self, instruction: CircuitInstruction) -> None:
        """Handle CX instruction."""
        control_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        target_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[1])
        control_physical_data_register = self.physical_data_registers[control_logical_qubit_index]
        target_physical_data_register = self.physical_data_registers[target_logical_qubit_index]

        self.transpiled_qc.cx(
            control_physical_data_register,
            target_physical_data_register,
        )

        self.transpiled_qc.barrier(label=f"CX {control_logical_qubit_index} {target_logical_qubit_index}")

        if self.add_syndromes:
            self.insert_syndromes(control_logical_qubit_index)
            self.insert_syndromes(target_logical_qubit_index)

    # it could use the hadamards with cnots
    def _handle_cz(self, instruction: CircuitInstruction) -> None:
        """Handle CZ instruction."""
        control_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        target_logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[1])
        control_physical_data_register = self.physical_data_registers[control_logical_qubit_index]
        target_physical_data_register = self.physical_data_registers[target_logical_qubit_index]

        self.transpiled_qc.cz(
            control_physical_data_register,
            target_physical_data_register,
        )

        self.transpiled_qc.barrier(label=f"CZ {control_logical_qubit_index} {target_logical_qubit_index}")

        if self.add_syndromes:
            self.insert_syndromes(control_logical_qubit_index)
            self.insert_syndromes(target_logical_qubit_index)

    # TODO: Review and verify it works
    def insert_syndromes(self, logical_qubit_index: int) -> None:
        """Automate the insertion of the measurement and correction cycles."""
        physical_data_register = self.physical_data_registers[logical_qubit_index]
        bit_flip_syndrome_register = self.bit_flip_syndromes[logical_qubit_index]
        phase_flip_syndrome_register = self.phase_flip_syndromes[logical_qubit_index]
        bit_flip_measurement_register = self.bit_flip_syndrome_measurements[logical_qubit_index]
        phase_flip_measurement_register = self.phase_flip_syndrome_measurements[logical_qubit_index]

        self.transpiled_qc.barrier(label="Syndrome Start")

        # clean ancillas
        self.transpiled_qc.reset(bit_flip_syndrome_register)
        self.transpiled_qc.reset(phase_flip_syndrome_register)

        # Syndrome extraction
        self.transpiled_qc.compose(
            get_seven_qubit_steane_code_syndrome_extraction_circuit(),
            qubits=physical_data_register[:] + bit_flip_syndrome_register[:] + phase_flip_syndrome_register[:],
            inplace=True,
        )

        self.transpiled_qc.barrier()

        # Error correction
        apply_seven_qubit_steane_code_correction(
            self.transpiled_qc,
            physical_data_register,
            bit_flip_syndrome_register,
            phase_flip_syndrome_register,
            bit_flip_measurement_register,
            phase_flip_measurement_register,
        )

        self.transpiled_qc.barrier(label="Correction End")
