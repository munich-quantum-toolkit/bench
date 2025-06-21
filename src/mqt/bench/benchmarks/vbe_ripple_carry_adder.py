# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VBE Ripple-Carry Adder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.synthesis import adder_ripple_v95

from ._registry import register_benchmark

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit


@register_benchmark("vbe_ripple_carry_adder", description="Vedral-Barenco-Eker (VBE) Ripple-Carry Adder")
def create_circuit(num_qubits: int, kind: str = "full") -> QuantumCircuit:
    """Create a vbe ripple-carry adder circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit
            kind: The kind of adder, can be ``"full"`` for a full adder, ``"half"`` for a half
                adder, or ``"fixed"`` for a fixed-sized adder. A full adder includes both carry-in
                and carry-out, a half only carry-out, and a fixed-sized adder neither carry-in
                nor carry-out. Additionally, num_state_qubits - 1 ancillary qubits are added.
                For example if num_qubits=13 and kind="full", there is one qubit for carry-in, one qubit
                for carry-out, num_state_qubits=4 for each of the 2 registers, and num_state_qubits-1=3
                ancillary qubits.

    Returns:
           QuantumCircuit: The constructed vbe ripple-carry adder circuit.

    See Also:
        :class:`qiskit.circuit.library.VBERippleCarryAdder`
    """
    if kind == "half":
        if num_qubits % 3 or num_qubits < 3:
            msg = "num_qubits must be an integer ≥ 3 and divisible by 3."
            raise ValueError(msg)
        num_state_qubits = num_qubits // 2
    elif kind == "full":
        if (num_qubits - 1) % 3 or num_qubits < 4:
            msg = "num_qubits must be an integer ≥ 4 and (num_qubits - 1) must be divisible by 3."
            raise ValueError(msg)
        num_state_qubits = (num_qubits - 1) // 3
    elif kind == "fixed":
        if (num_qubits + 1) % 3 or num_qubits < 2:
            msg = "num_qubits must be an integer ≥ 2 and (num_qubits + 1) must be divisible by 3."
            raise ValueError(msg)
        num_state_qubits = (num_qubits + 1) // 3
    else:
        msg = "kind must be 'full', 'half', or 'fixed'."
        raise ValueError(msg)

    qc = adder_ripple_v95(num_state_qubits, kind)
    qc.measure_all()
    qc.name = "vbe_ripple_carry_adder"

    return qc
