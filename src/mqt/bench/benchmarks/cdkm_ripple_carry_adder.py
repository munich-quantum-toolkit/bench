# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""CDKM Ripple-Carry Adder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit import ClassicalRegister
from qiskit.synthesis import adder_ripple_c04

from ._registry import register_benchmark

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit


@register_benchmark("cdkm_ripple_carry_adder", description="Cuccaro-Draper-Kutin-Moulton (CDKM) Ripple-Carry Adder")
def create_circuit(num_qubits: int, kind: str = "full") -> QuantumCircuit:
    """Build a CDKM ripple-carry adder.

    Args:
        num_qubits: Total width. Full and half adders require an even width of at least 4.
            A fixed-width adder requires an odd width of at least 3.
        kind: ``"full"`` includes carry-in and carry-out, ``"half"`` includes only carry-out,
            and ``"fixed"`` retains only the low bits that fit in one operand. Half and fixed adders use a helper qubit.

    Returns:
        A circuit that measures only the sum into ``result``, least-significant bit first.
        For full and half addition, the highest result bit is the carry-out.

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
    result = ClassicalRegister(num_state_qubits + (kind != "fixed"), "result")
    qc.add_register(result)
    start = num_state_qubits + (kind == "full")
    qc.barrier()
    qc.measure(qc.qubits[start : start + len(result)], result)
    qc.name = "cdkm_ripple_carry_adder"

    return qc
