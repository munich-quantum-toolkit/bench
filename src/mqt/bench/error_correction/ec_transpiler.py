# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Base class for transpilers that encode circuits with a quantum error-correcting code."""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit import AncillaRegister, Gate, Instruction
from qiskit.synthesis import SolovayKitaevDecomposition
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.passes import OptimizeCliffordT

if TYPE_CHECKING:
    from qiskit.dagcircuit import DAGCircuit


class _SolovayKitaevRZ(TransformationPass):
    """Approximate each RZ rotation with Solovay-Kitaev at recursion degree 0.

    Recursion degree 0 picks the closest precomputed sequence of at most 12 H, T, and Tdg gates.
    ``OptimizeCliffordT`` then reduces the T count of this sequence, for example by merging T
    pairs into S gates. Unlike Qiskit's ``SolovayKitaev`` pass, this pass changes only RZ
    rotations, so Clifford gates such as Z do not become T gates.
    """

    def __init__(self) -> None:
        """Precompute the Solovay-Kitaev basic approximations."""
        super().__init__()
        self._decomposition = SolovayKitaevDecomposition()
        self._optimization = OptimizeCliffordT()

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Replace each RZ rotation in ``dag`` with its approximation."""
        for node in dag.named_nodes("rz"):
            approximation = self._decomposition.run(node.op, recursion_degree=0, return_dag=True)
            dag.substitute_node_with_dag(node, self._optimization.run(approximation))
        return dag


@dataclass
class LogicalQubit:
    """Encapsulates the physical registers representing a single encoded logical qubit."""

    data: QuantumRegister
    bit_flip_syndrome: AncillaRegister
    phase_flip_syndrome: AncillaRegister
    bit_flip_measure: ClassicalRegister
    phase_flip_measure: ClassicalRegister

    def get_all_registers(self) -> list[QuantumRegister | ClassicalRegister]:
        """Return all active registers for this logical qubit."""
        regs: list[QuantumRegister | ClassicalRegister] = [self.data]
        if self.bit_flip_syndrome is not None:
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


class ECTranspiler(ABC):
    """Encodes a QuantumCircuit with a quantum error-correcting code.

    Subclasses declare the code's parameters as class attributes and implement the abstract
    methods.
    """

    #: Short name of the code, used to name the encoded circuit and its placeholders.
    CODE_NAME: ClassVar[str]
    #: Number of physical qubits used to encode a single logical qubit.
    BLOCK_SIZE: ClassVar[int]
    #: Number of ancilla qubits (and classical bits) used per bit-flip syndrome extraction.
    BIT_FLIP_SYNDROME_SIZE: ClassVar[int]
    #: Number of ancilla qubits (and classical bits) used per phase-flip syndrome extraction.
    PHASE_FLIP_SYNDROME_SIZE: ClassVar[int]
    #: Basis gate set the original circuit is transpiled to before logical replacement.
    TARGET_GATE_SET: ClassVar[list[str]]
    #: Transversal gates: each one is realized by applying one physical gate at every physical
    #: qubit position of the involved data registers. Implement other gates as
    #: ``_logical_<gate_name>`` methods on the subclass.
    TRANSVERSAL_GATES: ClassVar[dict[str, Gate]] = {}

    def __init__(self, original_circuit: QuantumCircuit) -> None:
        """Initialize the transpiler with the original QuantumCircuit.

        Args:
            original_circuit: Original circuit to transpile using the error-correcting code.
        """
        self.original_qc = original_circuit
        self.num_logical_qubits = original_circuit.num_qubits
        self.logical_qubits: list[LogicalQubit] = []
        self.transpiled_qc = QuantumCircuit()
        self.encoded_qubits = [False for _ in range(self.num_logical_qubits)]

    def transpile(self) -> QuantumCircuit:
        """Encode the original circuit with the error-correcting code.

        The original circuit is first decomposed into the code's gate set, and rotations are
        approximated with Clifford+T sequences. The gate counts of the encoded circuit can
        therefore differ between Qiskit versions.

        Returns:
            The encoded circuit. It keeps a copy of the original circuit's metadata.
        """
        # reset before each transpilation
        self.logical_qubits: list[LogicalQubit] = []
        self.transpiled_qc = QuantumCircuit()
        self.encoded_qubits = [False for _ in range(self.num_logical_qubits)]

        for instruction in self.original_qc.data:
            if instruction.is_control_flow():
                msg = f"Error-correction transpilation currently does not support control-flow operations such as {instruction.operation.name}."
                raise ValueError(msg)

        self.original_qc = transpile(
            self.original_qc,
            basis_gates=self.TARGET_GATE_SET,
            optimization_level=0,
            approximation_degree=0.95,
            seed_transpiler=10,
        )

        self.encode_qubits()
        self.replace_gates()
        return self.transpiled_qc

    def encode_qubits(self) -> None:
        """Replace each logical qubit with a physical register and apply the code's encoding."""
        all_registers: list[QuantumRegister | ClassicalRegister] = []
        for i in range(self.num_logical_qubits):
            data_reg = QuantumRegister(self.BLOCK_SIZE, f"q{i}")
            logical_qubit = LogicalQubit(
                data=data_reg,
                bit_flip_syndrome=AncillaRegister(self.BIT_FLIP_SYNDROME_SIZE, f"bs{i}"),
                phase_flip_syndrome=AncillaRegister(self.PHASE_FLIP_SYNDROME_SIZE, f"ps{i}"),
                bit_flip_measure=ClassicalRegister(self.BIT_FLIP_SYNDROME_SIZE, f"bsm{i}"),
                phase_flip_measure=ClassicalRegister(self.PHASE_FLIP_SYNDROME_SIZE, f"psm{i}"),
            )

            self.logical_qubits.append(logical_qubit)
            all_registers.extend(logical_qubit.get_all_registers())

            self.encoded_qubits[i] = True

        self.transpiled_qc = QuantumCircuit(*all_registers)
        self.transpiled_qc.name = f"{self.original_qc.name}_{self.CODE_NAME}_encoded"
        # Qiskit's transpile() shares nested metadata values with its input circuit.
        self.transpiled_qc.metadata = deepcopy(self.original_qc.metadata)

        for logical_qubit in self.logical_qubits:
            self._apply_encoding(self.transpiled_qc, logical_qubit.data)

    def replace_gates(self) -> None:
        """Replace each instruction of the original circuit with its logical equivalent.

        Raises:
            ValueError: If an instruction uses a qubit after the qubit's measurement.
        """
        for instruction in self.original_qc.data:
            gate_name = instruction.operation.name
            logical_qubit_indices = [self.original_qc.qubits.index(q) for q in instruction.qubits]
            logical_clbit_indices = [self.original_qc.clbits.index(c) for c in instruction.clbits]

            # only check for actual instructions
            if gate_name != "barrier":
                decoded_qubits = [q for q in logical_qubit_indices if self.encoded_qubits[q] is False]
                if decoded_qubits:
                    msg = f"Instruction {gate_name} accesses qubits {decoded_qubits} after decoding"
                    raise ValueError(msg)

            self._apply_gate(gate_name, logical_qubit_indices, logical_clbit_indices)

    def _apply_gate(self, gate_name: str, logical_qubit_indices: list, logical_clbit_indices: list) -> None:
        """Apply a single named gate to the given logical qubit/classical-bit indices.

        Dispatch order:
        1. ``barrier`` and ``measure`` have generic handlers.
        2. A ``_logical_<gate_name>`` method on the subclass, if present.
        3. :attr:`TRANSVERSAL_GATES` (see :meth:`_apply_transversal_gate`).
        4. A placeholder (see :meth:`_handle_unregistered_gate`).
        """
        if gate_name == "barrier":
            self._handle_barrier(logical_qubit_indices)
            return
        if gate_name == "measure":
            self._handle_measure(logical_qubit_indices[0], logical_clbit_indices[0])
            return

        handler_name = f"_logical_{gate_name}"
        if hasattr(self, handler_name):
            getattr(self, handler_name)(*logical_qubit_indices)
        elif gate_name in self.TRANSVERSAL_GATES:
            self._apply_transversal_gate(self.TRANSVERSAL_GATES[gate_name], logical_qubit_indices)
        else:
            self._handle_unregistered_gate(gate_name, logical_qubit_indices)

    def _handle_barrier(self, logical_qubit_indices: list[int]) -> None:
        """Apply a logical barrier across the specified physical qubits."""
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

    def _handle_measure(self, logical_qubit_index: int, logical_classical_bit_index: int) -> None:
        """Decode a logical qubit and measure it into a fresh single-bit classical register."""
        self.encoded_qubits[logical_qubit_index] = False
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        self._apply_decoding(self.transpiled_qc, physical_data_register)

        measurement_register_name = f"meas_{logical_classical_bit_index}"

        # use existing classical register or create one
        physical_measurement_register = next(
            (reg for reg in self.transpiled_qc.cregs if reg.name == measurement_register_name), None
        )

        if physical_measurement_register is None:
            physical_measurement_register = ClassicalRegister(1, measurement_register_name)
            self.transpiled_qc.add_register(physical_measurement_register)

        self.transpiled_qc.measure(physical_data_register[0], physical_measurement_register[0])

    def _apply_transversal_gate(self, physical_gate: Gate, logical_qubit_indices: list[int]) -> None:
        """Apply ``physical_gate`` at every physical qubit position of the involved data registers.

        A syndrome cycle then runs on each involved logical qubit.
        """
        physical_data_registers = [self.logical_qubits[idx].data for idx in logical_qubit_indices]
        for physical_qubit_index in range(self.BLOCK_SIZE):
            physical_qubits = [register[physical_qubit_index] for register in physical_data_registers]
            self.transpiled_qc.append(physical_gate, physical_qubits)

        for logical_qubit_index in dict.fromkeys(logical_qubit_indices):
            self.insert_syndromes(logical_qubit_index)

    def _handle_unregistered_gate(self, gate_name: str, logical_qubit_indices: list[int]) -> None:
        """Realize a gate without a handler as a placeholder.

        An exact fault-tolerant realization of gates such as T needs magic-state injection or a
        similar costly construction. MQT Bench is concerned with the circuit structure, so it uses
        one opaque, ideal instruction on the involved data registers instead. The placeholder is
        named ``<CODE_NAME>_ideal_logical_<gate_name>``.
        """
        if gate_name not in self.TARGET_GATE_SET:
            msg = f"Error-correction transpilation currently does not support arbitrary gates such as {gate_name}. Currently supported: {self.TARGET_GATE_SET}"
            raise ValueError(msg)

        physical_data_registers = [self.logical_qubits[idx].data for idx in logical_qubit_indices]
        physical_qubits = [qubit for register in physical_data_registers for qubit in register]

        gadget = Instruction(
            name=f"{self.CODE_NAME}_ideal_logical_{gate_name}",
            num_qubits=len(physical_qubits),
            num_clbits=0,
            params=[],
        )
        self.transpiled_qc.append(gadget, physical_qubits)

        for logical_qubit_index in dict.fromkeys(logical_qubit_indices):
            self.insert_syndromes(logical_qubit_index)

    def insert_syndromes(self, logical_qubit_index: int) -> None:
        """Run the code's syndrome extraction and correction cycle on one logical qubit.

        The transpiler calls this method after every logical gate.

        Args:
            logical_qubit_index: Index of the logical qubit.
        """
        self._run_syndrome_cycle(self.logical_qubits[logical_qubit_index])

    @abstractmethod
    def _apply_encoding(self, qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply the code's encoding to a physical data register."""

    @abstractmethod
    def _apply_decoding(self, qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply the code's decoding to a physical data register."""

    @abstractmethod
    def _run_syndrome_cycle(self, qubit: LogicalQubit) -> None:
        """Reset ancillas, extract syndromes, and apply corrections for one logical qubit."""
