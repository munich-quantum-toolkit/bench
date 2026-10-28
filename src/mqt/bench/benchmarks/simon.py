# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Simon's algorithm benchmark definition."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("simon", description="Simon's Algorithm")
def create_circuit(num_qubits: int, hidden_string: str | None = None) -> QuantumCircuit:
    r"""Returns a quantum circuit implementing Simon's algorithm.

    Simon's algorithm (Simon 1997, SIAM J. Comput. 26, 1474) considers a function
    :math:`f: \{0,1\}^n \to \{0,1\}^n` with the promise that
    :math:`f(x) = f(y)` if and only if :math:`y = x` or :math:`y = x \oplus s`
    for a hidden, non-zero bitstring :math:`s`. The circuit uses two registers of
    :math:`n` qubits each:

    1. Hadamard gates are applied to the :math:`n` input qubits.
    2. The oracle :math:`U_f` maps :math:`|x\rangle|0\rangle` to :math:`|x\rangle|f(x)\rangle`.
       Here, :math:`f(x) = x \oplus x_j \cdot s`, where :math:`j` is the position of the
       first set bit of :math:`s`.
    3. Hadamard gates are applied to the input qubits again.
    4. The input qubits are measured. Every measured bitstring :math:`y`
       satisfies :math:`y \cdot s = 0 \pmod 2`.

    Arguments:
        num_qubits: Total number of qubits of the returned quantum circuit
            (input register plus output register). Must be even and at least 2.
        hidden_string: Hidden bitstring :math:`s`. Its length must be ``num_qubits / 2`` and it must
            contain at least one ``'1'``. The character ``hidden_string[i]`` belongs to input qubit
            :math:`q_i`. If None, defaults to an alternating pattern starting with ``'1'``.

    Returns:
        A quantum circuit implementing Simon's algorithm.
    """
    if num_qubits < 2 or num_qubits % 2 != 0:
        msg = "num_qubits must be an even integer ≥ 2."
        raise ValueError(msg)

    n = num_qubits // 2

    if hidden_string is None:
        hidden_string = "".join("1" if i % 2 == 0 else "0" for i in range(n))

    if len(hidden_string) != n or not set(hidden_string).issubset({"0", "1"}):
        msg = f"Invalid hidden_string '{hidden_string}'. Must be a binary string of length {n}."
        raise ValueError(msg)

    if "1" not in hidden_string:
        msg = "hidden_string must contain at least one '1'."
        raise ValueError(msg)

    inputs = QuantumRegister(n, "q")
    outputs = QuantumRegister(n, "out")
    c = ClassicalRegister(n, "c")
    qc = QuantumCircuit(inputs, outputs, c, name="simon")

    qc.h(inputs)
    qc.barrier()

    # Oracle: copy the input register and, conditioned on x_j, XOR in the hidden string.
    for i in range(n):
        qc.cx(inputs[i], outputs[i])
    j = hidden_string.index("1")
    for i, bit in enumerate(hidden_string):
        if bit == "1":
            qc.cx(inputs[j], outputs[i])
    qc.barrier()

    qc.h(inputs)
    qc.measure(inputs, c)

    return qc
