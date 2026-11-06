# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VBE Ripple-Carry Adder."""

from __future__ import annotations

from qiskit.circuit import AncillaRegister, ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.synthesis import adder_ripple_v95

from ._registry import register_benchmark


@register_benchmark("vbe_ripple_carry_adder", description="Vedral-Barenco-Eker (VBE) Ripple-Carry Adder")
def create_circuit(num_qubits: int, kind: str = "full") -> QuantumCircuit:
    """Create a vbe ripple-carry adder circuit.

    Measure only the sum into ``result``, least-significant bit first.
    Carry-out, when present, is the most-significant result bit.

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
        num_state_qubits = num_qubits // 3
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

    qc = _fixed_adder(num_state_qubits) if kind == "fixed" else adder_ripple_v95(num_state_qubits, kind)
    result = ClassicalRegister(num_state_qubits + (kind != "fixed"), "result")
    qc.add_register(result)
    start = num_state_qubits + (kind == "full")
    qc.barrier()
    qc.measure(qc.qubits[start : start + len(result)], result)
    qc.name = "vbe_ripple_carry_adder"

    return qc


def _fixed_adder(width: int) -> QuantumCircuit:
    """Construct fixed-width VBE addition with the carry entering the last bit.

    Qiskit's fixed-width implementation uses the preceding carry instead:
    https://github.com/Qiskit/qiskit/pull/16700.
    """
    a, b = QuantumRegister(width, "a"), QuantumRegister(width, "b")
    circuit = QuantumCircuit(a, b)
    if width == 1:
        circuit.cx(a[0], b[0])
        return circuit

    carry = AncillaRegister(width - 1, "helper")
    circuit.add_register(carry)
    circuit.ccx(a[0], b[0], carry[0])
    for i in range(1, width - 1):
        circuit.ccx(a[i], b[i], carry[i])
        circuit.cx(a[i], b[i])
        circuit.ccx(carry[i - 1], b[i], carry[i])

    circuit.cx(a[-1], b[-1])
    circuit.cx(carry[-1], b[-1])

    for i in reversed(range(1, width - 1)):
        circuit.ccx(carry[i - 1], b[i], carry[i])
        circuit.cx(a[i], b[i])
        circuit.ccx(a[i], b[i], carry[i])
        circuit.cx(a[i], b[i])
        circuit.cx(carry[i - 1], b[i])
    circuit.ccx(a[0], b[0], carry[0])
    circuit.cx(a[0], b[0])
    return circuit
