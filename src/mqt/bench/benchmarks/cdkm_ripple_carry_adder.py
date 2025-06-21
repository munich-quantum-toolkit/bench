# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""CDKM Ripple-Carry Adder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.synthesis import adder_ripple_c04

from ._registry import register_benchmark

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit


@register_benchmark("cdkm_ripple_carry_adder", description="Cuccaro-Draper-Kutin-Moulton (CDKM) Ripple-Carry Adder")
def create_circuit(num_qubits: int, kind: str = "full") -> QuantumCircuit:
    """Create a CDKM ripple-carry adder circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit
            kind: The kind of adder, can be ``"full"`` for a full adder, ``"half"`` for a half
               adder, or ``"fixed"`` for a fixed-sized adder. A full adder includes both carry-in
               and carry-out, a half ader only carry-out, but an additional helper qubit, and a fixed-sized
               adder neither carry-in or carry-out, but also has an additional helper qubit.

    Returns:
           QuantumCircuit: The constructed CDKM ripple-carry adder circuit.

    See Also:
        :class:`qiskit.circuit.library.CDKMRippleCarryAdder`
    """
    if kind in ["half", "full"]:
        if num_qubits % 2 or num_qubits < 4:
            msg = "num_qubits must be an even integer ≥ 4."
            raise ValueError(msg)

        num_state_qubits = num_qubits // 2 - 1
    elif kind == "fixed":
        if num_qubits % 2 == 0 or num_qubits < 3:
            msg = "num_qubits must be an odd integer ≥ 3."
            raise ValueError(msg)

        num_state_qubits = (num_qubits - 1) // 2
    else:
        msg = "kind must be 'full', 'half', or 'fixed'."
        raise ValueError(msg)

    qc = adder_ripple_c04(num_state_qubits, kind)
    qc.measure_all()
    qc.name = "cdkm_ripple_carry_adder"

    return qc
