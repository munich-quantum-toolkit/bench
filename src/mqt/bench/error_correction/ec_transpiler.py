# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Shared base transpiler for converting standard circuits into fault-tolerant circuits.

Concrete error-correcting codes (e.g. Shor's 9-qubit code, the 7-qubit Steane code) subclass
:class:`ECTranspiler` and only need to declare their gate set and provide the code-specific
encoding/decoding/syndrome circuits plus handlers for gates whose logical realization is not a
plain transversal application of a single physical gate. Any gate that is part of a subclass's
target gate set but has no dedicated handler is automatically realized as an opaque, ideal logical
gadget (see :meth:`ECTranspiler._handle_unregistered_gate`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit import AncillaRegister, Gate, Instruction


@dataclass
class LogicalQubit:
    """Encapsulates the physical registers representing a single encoded logical qubit."""

    data: QuantumRegister
    bit_flip_syndrome: AncillaRegister | None = None
    phase_flip_syndrome: AncillaRegister | None = None
    bit_flip_measure: ClassicalRegister | None = None
    phase_flip_measure: ClassicalRegister | None = None

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
    """A high-level transpiler that encodes a QuantumCircuit using a quantum error-correcting code.

    Subclasses declare the code's parameters as class attributes and implement the abstract
    methods below; :meth:`transpile`, :meth:`encode_qubits` and :meth:`replace_gates` are shared
    by every code.
    """

    #: Short name of the code, used e.g. to name the encoded circuit and opaque logical gadgets.
    CODE_NAME: ClassVar[str]
    #: Number of physical qubits used to encode a single logical qubit.
    BLOCK_SIZE: ClassVar[int]
    #: Number of ancilla qubits (and classical bits) used per bit-flip syndrome extraction.
    BIT_FLIP_SYNDROME_SIZE: ClassVar[int]
    #: Number of ancilla qubits (and classical bits) used per phase-flip syndrome extraction.
    PHASE_FLIP_SYNDROME_SIZE: ClassVar[int]
    #: Basis gate set the original circuit is transpiled to before logical replacement.
    TARGET_GATE_SET: ClassVar[list[str]]
    #: Gates that are realized by applying a single physical gate transversally, i.e. once per
    #: physical qubit position across all involved logical qubits' data registers. Gates that need
    #: a different physical realization (e.g. because control/target are inverted, or because the
    #: logical operator only acts on a subset of physical qubits) should instead be implemented as
    #: a dedicated ``_logical_<gate_name>`` method on the subclass.
    TRANSVERSAL_GATES: ClassVar[dict[str, Gate]] = {}
    #: Gates that are realized as a fixed sequence of other, already-specified gates. Each
    #: entry maps a gate name to a list of ``(sub_gate_name, qubit_map, clbit_map)`` steps, where
    #: ``qubit_map``/``clbit_map`` are indices into the *derived* gate's own qubit/clbit list.
    #: A derived gate may reference other handlers, transversal gates, or derived gates,
    #: but must not reference itself (directly or through other derived gates).
    #: E.g. ``{"swap": [("cx", [0, 1], []), ("cx", [1, 0], []), ("cx", [0, 1], [])]}``.
    DERIVED_GATES: ClassVar[dict[str, list[tuple[str, list[int], list[int]]]]] = {}

    def __init__(self, original_circuit: QuantumCircuit, *, add_syndromes: bool = True) -> None:
        """Initialize the transpiler with the original QuantumCircuit.

        Args:
            original_circuit: Original circuit to transpile using the error-correcting code.
            add_syndromes: Whether to insert syndrome extraction and correction cycles.
        """
        self.original_qc = original_circuit
        self.num_logical_qubits = original_circuit.num_qubits
        self.add_syndromes = add_syndromes
        self.logical_qubits: list[LogicalQubit] = []
        # TODO: is it weird, that we're only doing this for t-gates? potentially reconfigure to more adaptive data structure
        self.t_gate_count = 0
        self.transpiled_qc = QuantumCircuit()

        # We need this for backwards compatibility with the testing suite
        self.physical_data_registers: list[QuantumRegister] = []

    def transpile(self) -> QuantumCircuit:
        """Transpile the original circuit to a fault-tolerant circuit using the error-correcting code.

        High-level Qiskit instructions such as ``QFTGate`` are first decomposed into the code's
        supported basis gates. For QFT, this decomposition currently uses
        ``approximation_degree=0.95``, so encoded QFT circuits are approximate rather than exact.

        Returns:
             The transpiled fault-tolerant circuit.
        """
        self.original_qc = transpile(
            self.original_qc,
            basis_gates=self.TARGET_GATE_SET,
            optimization_level=3,
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
            self.physical_data_registers.append(data_reg)

            if self.add_syndromes:
                logical_qubit = LogicalQubit(
                    data=data_reg,
                    bit_flip_syndrome=AncillaRegister(self.BIT_FLIP_SYNDROME_SIZE, f"bs{i}"),
                    phase_flip_syndrome=AncillaRegister(self.PHASE_FLIP_SYNDROME_SIZE, f"ps{i}"),
                    bit_flip_measure=ClassicalRegister(self.BIT_FLIP_SYNDROME_SIZE, f"bsm{i}"),
                    phase_flip_measure=ClassicalRegister(self.PHASE_FLIP_SYNDROME_SIZE, f"psm{i}"),
                )
            else:
                logical_qubit = LogicalQubit(data=data_reg)

            self.logical_qubits.append(logical_qubit)
            all_registers.extend(logical_qubit.get_all_registers())

        self.transpiled_qc = QuantumCircuit(*all_registers)
        self.transpiled_qc.name = f"{self.original_qc.name}_{self.CODE_NAME}_encoded"

        for logical_qubit in self.logical_qubits:
            self._apply_encoding(self.transpiled_qc, logical_qubit.data)

    def replace_gates(self) -> None:
        """Scan the original circuit and dispatch each instruction to its logical equivalent.

        For every instruction, the original circuit's qubits/clbits are resolved to logical
        indices and handed off to :meth:`_apply_gate`, which owns the actual dispatch logic.
        """
        # TODO: add entry guards for decoded qubits. This should be handled in ec_transpiler
        # (i.e. right here)
        for instruction in self.original_qc.data:
            gate_name = instruction.operation.name
            logical_qubit_indices = [self.original_qc.qubits.index(q) for q in instruction.qubits]
            logical_clbit_indices = [self.original_qc.clbits.index(c) for c in instruction.clbits]

            self._apply_gate(gate_name, logical_qubit_indices, logical_clbit_indices)

    def _apply_gate(self, gate_name: str, logical_qubit_indices: list, logical_clbit_indices: list) -> None:
        """Apply a single named gate to the given logical qubit/classical-bit indices.

        Dispatch order:
        1. ``barrier``/``measure`` are always handled generically.
        2. A dedicated ``_logical_<gate_name>`` method on the subclass, if present, is used. This
           covers gates whose physical realization is not a plain transversal application of a
           single gate (e.g. a code-specific CX).
        3. Otherwise, if the gate is listed in :attr:`TRANSVERSAL_GATES`, it is applied
           transversally (see :meth:`_apply_transversal_gate`).
        4. Otherwise, if the gate is listed in :attr:`DERIVED_GATES`, it is expanded into its
           declared sequence of sub-gates (see :meth:`_apply_derived_gate`).
        5. Otherwise, the gate is realized as an opaque, ideal logical gadget (see
           :meth:`_handle_unregistered_gate`).
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
        elif gate_name in self.DERIVED_GATES:
            self._apply_derived_gate(gate_name, logical_qubit_indices, [])
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
        physical_data_register = self.logical_qubits[logical_qubit_index].data
        self._apply_decoding(self.transpiled_qc, physical_data_register)

        measurement_register_name = f"meas_{logical_qubit_index}_{logical_classical_bit_index}"
        physical_measurement_register = ClassicalRegister(1, measurement_register_name)
        self.transpiled_qc.add_register(physical_measurement_register)

        self.transpiled_qc.measure(physical_data_register[0], physical_measurement_register[0])

    def _apply_transversal_gate(self, physical_gate: Gate, logical_qubit_indices: list[int]) -> None:
        """Apply ``physical_gate`` once per physical qubit position across the involved blocks.

        This is the shared building block behind :attr:`TRANSVERSAL_GATES` and can also be reused
        by subclasses to implement gates that decompose into a sequence of transversal gates (e.g.
        SWAP or DCX built from transversal CX applications).
        """
        physical_data_registers = [self.logical_qubits[idx].data for idx in logical_qubit_indices]
        for physical_qubit_index in range(self.BLOCK_SIZE):
            physical_qubits = [register[physical_qubit_index] for register in physical_data_registers]
            self.transpiled_qc.append(physical_gate, physical_qubits)

        for logical_qubit_index in dict.fromkeys(logical_qubit_indices):
            self.insert_syndromes(logical_qubit_index)

    def _apply_derived_gate(
        self, gate_name: str, logical_qubit_indices: list[int], logical_clbit_indices: list[int]
    ) -> None:
        """Apply a gate declared in :attr:`DERIVED_GATES` as a sequence of other gates.

        Each declared step is a ``(sub_gate_name, qubit_map, clbit_map)`` tuple, where
        ``qubit_map``/``clbit_map`` index into ``logical_qubit_indices``/``logical_clbit_indices``
        (the qubits/clbits the *derived* gate was itself invoked on) to build the logical indices
        for that step. Each step applies its gate through :meth:`_apply_gate`, so a sub-gate may
        itself be transversal, another derived gate, or have a dedicated ``_logical_<name>`` handler.

        Note: this does not guard against a gate (directly or transitively) deriving from itself.
        """
        if self.DERIVED_GATES[gate_name] is not None:
            for gate, qubit_map, clbit_map in self.DERIVED_GATES[gate_name]:
                mapped_qubit_indices = [logical_qubit_indices[i] for i in qubit_map]
                mapped_clbit_indices = [logical_clbit_indices[i] for i in clbit_map]
                self._apply_gate(gate, mapped_qubit_indices, mapped_clbit_indices)
        else:
            msg = f"No derivation specified for derived gate {self.DERIVED_GATES[gate_name]}."
            raise ValueError(msg)

    def _handle_unregistered_gate(self, gate_name: str, logical_qubit_indices: list[int]) -> None:
        """Realize a gate with no dedicated handler as an opaque, ideal logical gadget.

        Many logical gates (e.g. T, or a code's non-transversal Hadamard) require magic-state
        injection or another resource-intensive fault-tolerant construction to implement exactly.
        Since this benchmark suite is only concerned with the resulting circuit *structure*, such
        gates are instead represented by a single opaque, ideal placeholder instruction spanning
        the involved logical qubits' data registers, named
        ``f"{CODE_NAME}_logical_{gate_name}_magic_state_injection"``.
        """
        if gate_name in {"t", "tdg"}:
            self.t_gate_count += 1

        physical_data_registers = [self.logical_qubits[idx].data for idx in logical_qubit_indices]
        physical_qubits = [qubit for register in physical_data_registers for qubit in register]

        gadget = Instruction(
            name=f"{self.CODE_NAME}_logical_{gate_name}_magic_state_injection",
            num_qubits=len(physical_qubits),
            num_clbits=0,
            params=[],
        )
        self.transpiled_qc.append(gadget, physical_qubits)

        for logical_qubit_index in dict.fromkeys(logical_qubit_indices):
            self.insert_syndromes(logical_qubit_index)

    def insert_syndromes(self, logical_qubit_index: int) -> None:
        """Run the code's syndrome extraction and correction cycle for one logical qubit's block.

        This method is called automatically after every logical gate if the transpiler was
        constructed with ``add_syndromes=True``.

        Args:
            logical_qubit_index: Index of the logical qubit whose data block should undergo the
                correction cycle.
        """
        if not self.add_syndromes:
            return
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
