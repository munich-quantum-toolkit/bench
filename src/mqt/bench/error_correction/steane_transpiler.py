# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Steane Transpiler for converting standard circuits into fault-tolerant circuits using the 7-qubit Steane code."""

from __future__ import annotations

from typing import ClassVar

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit import AncillaRegister, CircuitInstruction, Gate
from qiskit.circuit.library import (
    CXGate,
    CZGate,
    HGate,
    IGate,
    SdgGate,
    SGate,
    XGate,
    YGate,
    ZGate,
)

from mqt.bench.components.steane_circuit_components import (
    apply_seven_qubit_steane_code_correction,
    get_seven_qubit_steane_code_decoding_circuit,
    get_seven_qubit_steane_code_encoding_circuit,
    get_seven_qubit_steane_code_syndrome_extraction_circuit,
)


class SteaneTranspiler:
    """A high-level transpiler that encodes a QuantumCircuit using Steane's 7-qubit error correction code."""

    TRANSVERSAL_PHYSICAL_GATES: ClassVar[dict[str, Gate]] = {
        "id": IGate(),
        "x": XGate(),
        "y": YGate(),
        "z": ZGate(),
        "h": HGate(),
        # Our Steane convention:
        # logical S   = physical Sdg on every qubit
        # logical Sdg = physical S on every qubit
        "s": SdgGate(),
        "sdg": SGate(),
        "cx": CXGate(),
        "cz": CZGate(),
    }

    def __init__(self, original_circuit: QuantumCircuit, *, add_syndromes: bool = True) -> None:
        """Initialize the transpiler with the original QuantumCircuit."""
        self.original_qc = original_circuit
        self.num_logical_qubits = original_circuit.num_qubits
        self.physical_data_registers: list[QuantumRegister] = []
        self.bit_flip_syndromes: list[AncillaRegister] = []
        self.phase_flip_syndromes: list[AncillaRegister] = []
        self.bit_flip_syndrome_measurements: list[ClassicalRegister] = []
        self.phase_flip_syndrome_measurements: list[ClassicalRegister] = []
        self.add_syndromes = add_syndromes
        self.t_gate_count = 0
        self.transpiled_qc = QuantumCircuit()
        self.gate_handlers = {
            "barrier": self._handle_barrier,
            "measure": self._handle_measure,
            "id": self._handle_transversal,
            "x": self._handle_transversal,
            "y": self._handle_transversal,
            "z": self._handle_transversal,
            "h": self._handle_transversal,
            "s": self._handle_transversal,
            "sdg": self._handle_transversal,
            "cx": self._handle_transversal,
            "cz": self._handle_transversal,
            "cy": self._handle_cy,
            "swap": self._handle_swap,
            "dcx": self._handle_dcx,
            "t": self._handle_t,
            "tdg": self._handle_tdg,
        }

    def transpile(self) -> QuantumCircuit:
        """Transpile the original circuit to a fault-tolerant circuit using Steane's code.

        High-level Qiskit instructions such as ``QFTGate`` are first decomposed
        into the supported basis gates. For QFT, this decomposition currently
        uses ``approximation_degree=0.95``, so encoded QFT circuits are
        approximate rather than exact.

        Returns:
             The transpiled fault-tolerant circuit.
        """
        # Firstly, expand high level gates, such as QFTGate()
        self.original_qc = transpile(
            self.original_qc,
            basis_gates=[
                "id",
                "x",
                "y",
                "z",
                "h",
                "s",
                "sdg",
                "cx",
                "sx",
                "sxdg",
                "cy",
                "cz",
                "swap",
                "dcx",
                "t",
                "tdg",
            ],
            optimization_level=3,
            approximation_degree=0.95,
            seed_transpiler=10,
        )

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

    def replace_gates(self) -> None:
        """Scan the original circuit and replace gates with logical equivalents.

        High-level gates are normalized before logical encoding. In particular,
        ``QFTGate`` instructions are transpiled to the supported
        ``["id", "x", "y", "z", "h", "s", "sdg", "cx", "sx", "sxdg", "cy", "cz", "swap", "dcx", "t", "tdg"]`` basis with
        ``approximation_degree=0.95``. This means QFT instructions are encoded
        as approximate circuits rather than exact QFT implementations.
        """
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
        for q in instruction.qubits:
            logical_qubit_index = self.original_qc.qubits.index(q)
            physical_data_register = self.physical_data_registers[logical_qubit_index]
            bit_flip_syndromes_register = self.bit_flip_syndromes[logical_qubit_index]
            phase_flip_syndromes_register = self.phase_flip_syndromes[logical_qubit_index]
            barrier_register.extend([
                physical_data_register,
                bit_flip_syndromes_register,
                phase_flip_syndromes_register,
            ])
        self.transpiled_qc.barrier(*barrier_register, label="Barrier")

    def _handle_measure(self, instruction: CircuitInstruction) -> None:
        """Handle measure instruction."""
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

    def _handle_transversal(self, instruction: CircuitInstruction) -> None:
        """Apply a logical gate transversally to its physical Steane blocks."""
        operation_name = instruction.operation.name

        try:
            physical_operation = self.TRANSVERSAL_PHYSICAL_GATES[operation_name]
        except KeyError as error:
            msg = f"Gate '{operation_name}' is not configured as transversal."
            raise ValueError(msg) from error

        logical_qubit_indices = [self.original_qc.qubits.index(qubit) for qubit in instruction.qubits]

        physical_data_registers = [self.physical_data_registers[index] for index in logical_qubit_indices]

        block_size = len(physical_data_registers[0])
        for physical_qubit_index in range(block_size):
            physical_qubits = [register[physical_qubit_index] for register in physical_data_registers]

            self.transpiled_qc.append(
                physical_operation,
                physical_qubits,
            )

        if self.add_syndromes:
            for logical_qubit_index in dict.fromkeys(logical_qubit_indices):
                self.insert_syndromes(logical_qubit_index)

    def _handle_cy(self, instruction: CircuitInstruction) -> None:
        """Implement CY gate via S and Sdg on target and CX inbetween."""
        self._handle_transversal(
            CircuitInstruction(
                operation=SteaneTranspiler.TRANSVERSAL_PHYSICAL_GATES["s"],
                qubits=instruction.qubits[1],
                clbits=(),
            )
        )
        self._handle_transversal(instruction)
        self._handle_transversal(
            CircuitInstruction(
                operation=SteaneTranspiler.TRANSVERSAL_PHYSICAL_GATES["sdg"],
                qubits=instruction.qubits[1],
                clbits=(),
            )
        )

    def _handle_swap(self, instruction: CircuitInstruction) -> None:
        """Implement Swap via 3 CX."""
        self._handle_transversal(
            CircuitInstruction(
                operation=SteaneTranspiler.TRANSVERSAL_PHYSICAL_GATES["cx"],
                qubits=instruction.qubits[:-1],
                clbits=(),
            )
        )
        self._handle_transversal(
            CircuitInstruction(
                operation=SteaneTranspiler.TRANSVERSAL_PHYSICAL_GATES["cx"],
                qubits=instruction.qubits,
                clbits=(),
            )
        )
        self._handle_transversal(
            CircuitInstruction(
                operation=SteaneTranspiler.TRANSVERSAL_PHYSICAL_GATES["cx"],
                qubits=instruction.qubits[:-1],
                clbits=(),
            )
        )

    def _handle_dcx(self, instruction: CircuitInstruction) -> None:
        """Implement CY gate via S and Sdg on target and CX inbetween."""
        self._handle_transversal(
            CircuitInstruction(
                operation=SteaneTranspiler.TRANSVERSAL_PHYSICAL_GATES["cx"],
                qubits=instruction.qubits,
                clbits=(),
            )
        )
        self._handle_transversal(
            CircuitInstruction(
                operation=SteaneTranspiler.TRANSVERSAL_PHYSICAL_GATES["cx"],
                qubits=instruction.qubits[:-1],
                clbits=(),
            )
        )

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

        # apply if_test
        with self.transpiled_qc.if_test((t_test_register[0], 1)):
            self.transpiled_qc.sdg(physical_data_register)

        if self.add_syndromes:
            self.insert_syndromes(logical_qubit_index)

    def _handle_tdg(self, instruction: CircuitInstruction) -> None:
        """Handle Tdg instruction."""
        logical_qubit_index = self.original_qc.qubits.index(instruction.qubits[0])
        physical_data_register = self.physical_data_registers[logical_qubit_index]

        t_ancilla_register = AncillaRegister(7, f"tdg{self.t_gate_count}")
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

        # apply physical tdg gates
        self.transpiled_qc.tdg(t_ancilla_register)

        # logical cnot from data to ancilla
        self.transpiled_qc.cx(physical_data_register, t_ancilla_register)

        # made logical measurement
        self.transpiled_qc.compose(
            get_seven_qubit_steane_code_decoding_circuit(), qubits=t_ancilla_register, inplace=True
        )
        self.transpiled_qc.measure(t_ancilla_register[0], t_test_register[0])

        # apply if_test
        with self.transpiled_qc.if_test((t_test_register[0], 1)):
            self.transpiled_qc.s(physical_data_register)

        if self.add_syndromes:
            self.insert_syndromes(logical_qubit_index)

    def insert_syndromes(self, logical_qubit_index: int) -> None:
        """Automate the insertion of the measurement and correction cycles."""
        physical_data_register = self.physical_data_registers[logical_qubit_index]
        bit_flip_syndrome_register = self.bit_flip_syndromes[logical_qubit_index]
        phase_flip_syndrome_register = self.phase_flip_syndromes[logical_qubit_index]
        bit_flip_measurement_register = self.bit_flip_syndrome_measurements[logical_qubit_index]
        phase_flip_measurement_register = self.phase_flip_syndrome_measurements[logical_qubit_index]

        # clean ancillas
        self.transpiled_qc.reset(bit_flip_syndrome_register)
        self.transpiled_qc.reset(phase_flip_syndrome_register)

        # Syndrome extraction
        self.transpiled_qc.compose(
            get_seven_qubit_steane_code_syndrome_extraction_circuit(),
            qubits=physical_data_register[:] + bit_flip_syndrome_register[:] + phase_flip_syndrome_register[:],
            inplace=True,
        )

        # Error correction
        apply_seven_qubit_steane_code_correction(
            self.transpiled_qc,
            physical_data_register,
            bit_flip_syndrome_register,
            phase_flip_syndrome_register,
            bit_flip_measurement_register,
            phase_flip_measurement_register,
        )
