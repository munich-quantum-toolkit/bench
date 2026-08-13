# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Steane Transpiler for converting standard circuits into fault-tolerant circuits using the 7-qubit Steane code."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

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

from .ec_transpiler import ECTranspiler, LogicalQubit

if TYPE_CHECKING:
    from qiskit import QuantumCircuit, QuantumRegister
    from qiskit.circuit import Gate


class SteaneTranspiler(ECTranspiler):
    """A high-level transpiler that encodes a QuantumCircuit using Steane's 7-qubit error correction code.

    Every gate in :attr:`TARGET_GATE_SET` except SWAP, DCX and CY is transversal in the strict
    sense used by :class:`ECTranspiler`, i.e. realized by applying a single physical gate once per
    physical qubit position. SWAP, DCX and CY are implemented in terms of the transversal CX/S/Sdg
    gates. T and Tdg have no dedicated handler and are therefore automatically realized as opaque,
    ideal logical gadgets by the base class.
    """

    CODE_NAME = "steane"
    BLOCK_SIZE = 7
    BIT_FLIP_SYNDROME_SIZE = 3
    PHASE_FLIP_SYNDROME_SIZE = 3
    TARGET_GATE_SET: ClassVar[list[str]] = [
        "id",
        "x",
        "y",
        "z",
        "h",
        "s",
        "sdg",
        "cx",
        "cy",
        "cz",
        "swap",
        "dcx",
        "t",
        "tdg",
    ]
    # Our Steane convention: logical S = physical Sdg on every qubit, logical Sdg = physical S on every qubit.
    TRANSVERSAL_GATES: ClassVar[dict[str, Gate]] = {
        "id": IGate(),
        "x": XGate(),
        "y": YGate(),
        "z": ZGate(),
        "h": HGate(),
        "s": SdgGate(),
        "sdg": SGate(),
        "cx": CXGate(),
        "cz": CZGate(),
    }
    DERIVED_GATES: ClassVar[dict[str, list[tuple[str, list[int], list[int]]]]] = {
        "swap": [("cx", [0, 1], []), ("cx", [1, 0], []), ("cx", [0, 1], [])],
        "cy": [("s", [1], []), ("cx", [0, 1], []), ("sdg", [1], [])],
        "dcx": [("cx", [0, 1], []), ("cx", [1, 0], [])],
    }

    def _apply_encoding(self, qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply Steane 7-qubit encoding to a physical data register."""
        qc.compose(
            get_seven_qubit_steane_code_encoding_circuit(),
            qubits=physical_data_register[:],
            inplace=True,
        )

    def _apply_decoding(self, qc: QuantumCircuit, physical_data_register: QuantumRegister) -> None:
        """Apply Steane 7-qubit decoding to a physical data register."""
        qc.compose(
            get_seven_qubit_steane_code_decoding_circuit(),
            qubits=physical_data_register[:],
            inplace=True,
        )

    def _run_syndrome_cycle(self, qubit: LogicalQubit) -> None:
        """Run the Steane code's syndrome extraction and correction cycle.

        1. **Ancilla preparation**: The syndrome ancilla registers are reset to |0>.
        2. **Syndrome extraction**: The bit-flip ancillas measure the Z-type stabilizers
        and the phase-flip ancillas measure the X-type stabilizers, mapping each error onto a 3-bit syndrome.
        3. **Correction**: The ancillas are measured into the corresponding classical syndrome registers,
        and X and Z corrections are applied to the identified data qubit.
        """
        if qubit.bit_flip_syndrome is None or qubit.phase_flip_syndrome is None:
            msg = "Syndrome registers are missing or not initialized."
            raise ValueError(msg)

        self.transpiled_qc.reset(qubit.bit_flip_syndrome)
        self.transpiled_qc.reset(qubit.phase_flip_syndrome)

        self.transpiled_qc.compose(
            get_seven_qubit_steane_code_syndrome_extraction_circuit(),
            qubits=qubit.data[:] + qubit.bit_flip_syndrome[:] + qubit.phase_flip_syndrome[:],
            inplace=True,
        )

        apply_seven_qubit_steane_code_correction(
            self.transpiled_qc,
            qubit.data,
            qubit.bit_flip_syndrome,
            qubit.phase_flip_syndrome,
            qubit.bit_flip_measure,
            qubit.phase_flip_measure,
        )
